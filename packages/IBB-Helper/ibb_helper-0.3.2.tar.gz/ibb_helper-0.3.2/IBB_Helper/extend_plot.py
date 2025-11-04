import matplotlib.pyplot as plt
import plotly.graph_objects as go
import copy
import numpy as np
from sympy import latex

def extend_plot(plot_list, dx=0, colors=None, labels=None, line_styles=None,
                 show=True, grid=False, xlim=None, ylim=None, title=None, 
                 xlabel=None, ylabel=None):
    """
    Generates a single continuous visual extension by stitching together curves 
    from multiple plots end-to-end, with optional horizontal offset dx.

    Args:
        plot_list (list): List of matplotlib Axes objects or Plotly Figure objects.
        dx (float): Horizontal offset to add between consecutive plots.
                   When dx=0, plots are stitched end-to-end with no gap.
                   When dx>0, creates gaps between plots.
                   When dx<0, creates overlap between plots.
        colors (list/str): Single color or list of colors for the plots.
        labels (list): Labels for the combined legend.
        [... other common plot options ...]

    Returns:
        matplotlib Axes object OR plotly Figure object.
    """

    # === SMART LABEL HELPER ===
    def smart_label(lbl):
        """Converts label or SymPy expression into LaTeX-compatible string."""
        if lbl is None:
            return None
        if isinstance(lbl, str):
            if any(c in lbl for c in ['_', '^', '\\']):
                return f"${lbl}$"
            else:
                return lbl
        else:
            return f"${latex(lbl)}$"
        
    if not plot_list:
        raise ValueError("Plot list cannot be empty")
    
    first_plot = plot_list[0]
    
    # === MATPLOTLIB AXES HANDLING (PRIMARY BRANCH) ===
    if hasattr(first_plot, 'lines') or hasattr(first_plot, 'get_lines'):
        fig, ax = plt.subplots()
        
        # Aggregation variables (for defaults if arguments are None)
        agg_xlim = [float('inf'), float('-inf')]
        
        # Use a single color if provided, or prepare for individual colors
        if isinstance(colors, str):
            colors = [colors] * len(plot_list)
        
        # Track the ending x position of the previous plot
        prev_plot_max_x = None
        
        for i, p in enumerate(plot_list):
            
            # Retrieve lines from Axes or Figure
            if hasattr(p, 'lines'):
                lines = p.lines
            elif hasattr(p, 'get_lines'):
                lines = p.get_lines()
            else:
                lines = []
            
            # First pass: find min and max x for this plot
            plot_min_x = float('inf')
            plot_max_x = float('-inf')
            
            for line in lines:
                x_orig, y_orig = line.get_data()
                if len(x_orig) > 0:
                    plot_min_x = min(plot_min_x, np.min(x_orig))
                    plot_max_x = max(plot_max_x, np.max(x_orig))
            
            # Calculate shift for this plot
            if i == 0:
                # First plot: no shift
                x_shift = 0
            else:
                # Subsequent plots: align min_x with prev_max_x + dx
                x_shift = prev_plot_max_x - plot_min_x + dx
            
            # --- Plotting ---
            for line_index, line in enumerate(lines):
                x_orig, y_orig = line.get_data()
                
                # Apply shift
                x = x_orig + x_shift
                y = y_orig
                
                # Default style transfer from source line
                plot_color = colors[i] if colors and i < len(colors) else line.get_color()
                
                # Get linestyle - handle marker-only plots
                orig_linestyle = line.get_linestyle()
                if orig_linestyle in ['None', '']:
                    orig_linestyle = ''
                plot_style = line_styles[i] if line_styles and i < len(line_styles) else orig_linestyle
                
                # Get marker - normalize 'None' string to empty
                plot_marker = line.get_marker()
                if plot_marker in ['None', '']:
                    plot_marker = ''

                # Label transfer (only the first line of the source plot gets the label)
                plot_label = labels[i] if labels and i < len(labels) and line_index == 0 else None
                
                # Plot the segment
                ax.plot(x, y, 
                        color=plot_color, 
                        linestyle=plot_style, 
                        marker=plot_marker,
                        markersize=line.get_markersize(),
                        linewidth=line.get_linewidth(),
                        label=plot_label)

                # Update global xlim
                if len(x) > 0:
                    agg_xlim[0] = min(agg_xlim[0], np.min(x))
                    agg_xlim[1] = max(agg_xlim[1], np.max(x))

            # Update previous plot's max x for next iteration
            if plot_max_x != float('-inf'):
                prev_plot_max_x = plot_max_x + x_shift


        # --- Final Matplotlib Configuration ---
        
        # Apply limits (prioritize argument, then aggregated data, then source plot limits)
        final_xlim = xlim if xlim else agg_xlim
        
        if ylim is None and hasattr(first_plot, 'get_ylim'):
            final_ylim = first_plot.get_ylim()
        else:
            final_ylim = ylim

        ax.set_xlim(final_xlim)
        if final_ylim:
             ax.set_ylim(final_ylim)

        # Apply labels/title (prioritize argument, then source plot labels)
        ax.set_title(smart_label(title) if title else (smart_label(first_plot.get_title()) if hasattr(first_plot, 'get_title') else ''))
        ax.set_xlabel(smart_label(xlabel) if xlabel else (smart_label(first_plot.get_xlabel()) if hasattr(first_plot, 'get_xlabel') else ''))
        ax.set_ylabel(smart_label(ylabel) if ylabel else (smart_label(first_plot.get_ylabel()) if hasattr(first_plot, 'get_ylabel') else ''))
        
        if grid:
            ax.grid(True)
        if labels: # Only show legend if we managed labels
            ax.legend()
            
        if show:
            plt.show()
        else:
            plt.close()

        return ax
    
    # === PLOTLY FIGURE HANDLING (SECONDARY BRANCH) ===
    elif hasattr(first_plot, 'data'):
        # Plotly branch
        combined_fig = go.Figure()
        prev_plot_max_x = None

        # Retrieve layout defaults from the first figure
        layout_defaults = first_plot.layout

        for i, fig in enumerate(plot_list):
            # First pass: find min and max x for this plot
            plot_min_x = float('inf')
            plot_max_x = float('-inf')
            
            for trace in fig.data:
                if hasattr(trace, 'x') and trace.x is not None:
                    x_data = np.array(trace.x)
                    if len(x_data) > 0:
                        plot_min_x = min(plot_min_x, np.min(x_data))
                        plot_max_x = max(plot_max_x, np.max(x_data))
            
            # Calculate shift for this plot
            if i == 0:
                x_shift = 0
            else:
                x_shift = prev_plot_max_x - plot_min_x + dx
            
            # Second pass: apply shift and add traces
            for trace in fig.data:
                # Use deepcopy for safe cloning
                new_trace = copy.deepcopy(trace)
                
                # Apply shift
                if hasattr(trace, 'x') and trace.x is not None:
                    x_data = np.array(trace.x)
                    new_trace.x = x_data + x_shift
                        
                # Apply overrides/defaults
                if colors and i < len(colors):
                    if hasattr(new_trace, 'line'):
                        new_trace.line.color = colors[i]
                    elif hasattr(new_trace, 'marker'):
                        new_trace.marker.color = colors[i]

                if line_styles and i < len(line_styles):
                    if hasattr(new_trace, 'line'):
                        new_trace.line.dash = line_styles[i]
                
                if labels and i < len(labels):
                    new_trace.name = smart_label(labels[i])
                
                combined_fig.add_trace(new_trace)
            
            # Update previous plot's max x for next iteration
            if plot_max_x != float('-inf'):
                prev_plot_max_x = plot_max_x + x_shift

        # Final Layout Configuration (prioritize arguments over defaults)
        combined_fig.update_layout(
                title=smart_label(title) if title else (smart_label(layout_defaults.title.text) if layout_defaults.title else ''),
                xaxis_title=smart_label(xlabel) if xlabel else (smart_label(layout_defaults.xaxis.title.text) if layout_defaults.xaxis.title else ''),
                yaxis_title=smart_label(ylabel) if ylabel else (smart_label(layout_defaults.yaxis.title.text) if layout_defaults.yaxis.title else '')
        )
        
        if xlim:
            combined_fig.update_xaxes(range=xlim)
        if ylim:
            combined_fig.update_yaxes(range=ylim)
        if grid:
            combined_fig.update_layout(xaxis_showgrid=True, yaxis_showgrid=True)
            
        if show:
            combined_fig.show()
    
        return combined_fig

    else:
        raise TypeError("Unknown plot object type passed to extend_plot.")