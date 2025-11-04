import matplotlib.pyplot as plt
import plotly.graph_objects as go
import copy
from   sympy import latex

def combine_plots(plot_list, labels=None, line_styles=None, colors=None,
                 swap_axes=False, show=True, grid=False,
                 xlim=None, ylim=None, title=None, xlabel=None, ylabel=None):
    """
    Combines multiple individual matplotlib Axes or plotly Figures into a single figure.
        
        This function intelligently detects the type of plot object (Matplotlib or Plotly)
        and merges all data onto a new, single canvas. It preserves the original styling
        of each plot by default, but allows for explicit overrides for the final output.

        Parameters
        ----------
        plot_list : list
            The list of plot objects to be combined. All plots must be of the same type.
            - Syntax: `[ax1, ax2]` or `[fig1, fig2]`
        
        labels : list[str], optional
            A list of new labels to override the existing ones for the legend.
            - Syntax: `['Plot A', 'Plot B']`

        line_styles : list[str], optional
            A list of new line styles to override the existing ones. Can also be used
            to force a marker style (e.g., 'o', 'x').
            - Syntax: `['solid', 'dashed', 'o', 'x']`

        colors : list[str], optional
            A list of new colors to override the existing ones.
            - Syntax: `['red', 'blue', '#FF5733']`

        swap_axes : bool, optional
            If True, the x and y data for all plots will be swapped.
            - Syntax: `True` or `False`

        show : bool, optional
            If True, displays the combined plot immediately. If False, the plot object
            is returned without being shown.
            - Syntax: `True` or `False`

        grid : bool, optional
            If True, displays a grid on the final combined plot.
            - Syntax: `True` or `False`

        xlim : tuple[float, float], optional
            Sets the x-axis limits for the combined plot.
            - Syntax: `(0, 10)`

        ylim : tuple[float, float], optional
            Sets the y-axis limits for the combined plot.
            - Syntax: `(-5, 5)`

        title : str, optional
            The main title for the combined plot.
            - Syntax: `"My Combined Plot"`

        xlabel : str, optional
            The x-axis label for the combined plot.
            - Syntax: `"Time (s)"`

        ylabel : str, optional
            The y-axis label for the combined plot.
            - Syntax: `"Value"`

        Returns
        -------
        matplotlib.axes.Axes or plotly.graph_objects.Figure
            The final combined plot object, either a Matplotlib Axes or a Plotly Figure,
            depending on the input.
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
        raise ValueError("plot_list cannot be empty")

    first_plot = plot_list[0]
    
    # Define marker symbols for internal check (same list used in plot_2d)
    marker_symbols = ['o', 's', '^', 'x', '*', 'D', 'p', '+', 'v', '<', '>', '1', '2', '3', '4']

    # === MATPLOTLIB AXES HANDLING ===
    if hasattr(first_plot, 'lines'):
        fig, ax = plt.subplots()
        
        for i, plot_ax in enumerate(plot_list):
            first_line = True
            
            for line in plot_ax.lines:
                x, y = line.get_data()

                # --- 1. Retrieve Existing Properties (Default Transfer) ---
                current_color = line.get_color()
                current_marker = line.get_marker()
                current_linestyle = line.get_linestyle()
                current_markersize = line.get_markersize()
                current_linewidth = line.get_linewidth()
                
                # Normalize marker: Convert 'None' string to None
                if current_marker in ['None', '']:
                    current_marker = None
                    
                # Normalize linestyle: Matplotlib stores '' for marker-only plots
                if current_linestyle in ['None', '']: 
                    current_linestyle = 'None' 

                # --- 2. Apply Overrides from append_plots Arguments (Only for First Line) ---
                if first_line:
                    # Override Line Style / Marker
                    if line_styles and i < len(line_styles):
                        new_style = line_styles[i]
                        
                        if new_style in marker_symbols:
                            # Case A: User forces a marker (e.g., 'o', 'x')
                            current_marker = new_style
                            current_linestyle = 'None' # Ensure linestyle is off
                        else:
                            # Case B: User forces a line style (e.g., '--', 'solid')
                            current_linestyle = new_style
                            current_marker = None # Clear the marker

                    # Override Color
                    if colors and i < len(colors):
                        current_color = colors[i]
                
                # Apply label only to the first line of the current plot_ax
                label_to_use = smart_label(labels[i]) if first_line and labels and i < len(labels) else None

                # --- 3. Plot on the New Axes ---
                if swap_axes:
                    ax.plot(y, x, 
                            color=current_color, 
                            linestyle=current_linestyle if current_linestyle != 'None' else '', 
                            marker=current_marker if current_marker else '',
                            markersize=current_markersize,
                            linewidth=current_linewidth,
                            label=label_to_use)
                else:
                    ax.plot(x, y, 
                            color=current_color, 
                            linestyle=current_linestyle if current_linestyle != 'None' else '', 
                            marker=current_marker if current_marker else '',
                            markersize=current_markersize,
                            linewidth=current_linewidth,
                            label=label_to_use)

                first_line = False

        # --- 4. Final Axis/Figure Configuration (Matplotlib) ---
        if xlim:
            ax.set_xlim(xlim)
        if ylim:
            ax.set_ylim(ylim)
        if title:
            ax.set_title(smart_label(title))
        if xlabel:
            ax.set_xlabel(smart_label(xlabel))
        if ylabel:
            ax.set_ylabel(smart_label(ylabel))
        if grid:
            ax.grid()
        if labels:
            ax.legend()
        if show:
            plt.show()
        else:
            plt.close(fig)

        return ax

    # === PLOTLY FIGURE HANDLING ===
    elif hasattr(first_plot, 'data'):
        combined_fig = go.Figure()
        
        for i, fig in enumerate(plot_list):
            for trace in fig.data:
                # Use deepcopy for safe cloning of the trace
                new_trace = copy.deepcopy(trace)

                # Apply colors if provided and trace supports it
                if colors and i < len(colors):
                    if hasattr(new_trace, 'line'):
                        new_trace.line.color = colors[i]
                    if hasattr(new_trace, 'marker'):
                        new_trace.marker.color = colors[i]

                # Apply line styles (dash) if provided
                if line_styles and i < len(line_styles):
                    if isinstance(new_trace, go.Scatter) and hasattr(new_trace, 'line'):
                        new_trace.line.dash = line_styles[i]

                # Apply labels/name
                if labels and i < len(labels):
                    new_trace.name = labels[i]
                
                # Handle Axis Swap (if requested)
                if swap_axes and hasattr(new_trace, 'x') and hasattr(new_trace, 'y'):
                     new_trace.x, new_trace.y = new_trace.y, new_trace.x

                combined_fig.add_trace(new_trace)

        # Final Layout Configuration (Plotly)
        if title:
            combined_fig.update_layout(title=smart_label(title))
        
        final_xlabel = smart_label(ylabel) if swap_axes and ylabel else smart_label(xlabel) if xlabel else None
        final_ylabel = smart_label(xlabel) if swap_axes and xlabel else smart_label(ylabel) if ylabel else None

        if final_xlabel or final_ylabel:
            combined_fig.update_layout(xaxis_title=final_xlabel,
                                       yaxis_title=final_ylabel)
        if xlim:
            combined_fig.update_xaxes(range=xlim if not swap_axes else ylim)
        if ylim:
            combined_fig.update_yaxes(range=ylim if not swap_axes else xlim)
        if grid:
            combined_fig.update_layout(xaxis_showgrid=True, yaxis_showgrid=True)

        if show:
            combined_fig.show()

        return combined_fig

    else:
        raise TypeError("Unknown plot object type passed to combine_plots.")