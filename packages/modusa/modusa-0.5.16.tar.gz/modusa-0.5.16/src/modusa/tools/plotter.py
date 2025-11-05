#!/usr/bin/env python3

#---------------------------------
# Author: Ankit Anand
# Date: 26/08/25
# Email: ankit0.anand0@gmail.com
#---------------------------------

from pathlib import Path
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import numpy as np
import fnmatch
import matplotlib.lines as mlines
import imageio.v2 as imageio
from io import BytesIO
from IPython.display import HTML, display
import base64

#===== Loading Devanagari font ========
def _load_devanagari_font():
    """
    Load devanagari font as it works for both English and Hindi.
    """
    
    # Path to your bundled font
    font_path = Path(__file__).resolve().parents[1] / "fonts" / "NotoSansDevanagari-Regular.ttf"
    
    # Register the font with matplotlib
    fm.fontManager.addfont(str(font_path))
    
    # Get the font family name from the file
    hindi_font = fm.FontProperties(fname=str(font_path))
    
    # Set as default rcParam
    mpl.rcParams['font.family'] = [hindi_font.get_name(), 'DejaVu Sans'] # Fallback to DejaVu Sans
    
    #==============
    
    
    
#============= Canvas ==================
class _Canvas:
    """
    Provides internal APIs to create
    useful canvas on which plotting will
    be done.

    This is not supposed to be used directly
    by users.

    Tier Layout
    Grid Layout    
    """
    def __init__(self):
        
        self.fig = None
        self.axs = None
        self.type = None
        
    def tiers(self, config, xlim, fig_width, abc, fig_num):
        """
        Generate tiers like canvas based on the configuration.

        Parameters
        ----------
        config: str
                - A string combination of "a" for auxilary, "s" for signal, "m" for matrix
                - Eg. "ams", "aa", "a", "sam" etc.
        xlim: tuple
                - (start, end) of xlim.
        fig_width: int
                - Figure width
        abc: bool
                - Assign each tier a character for referencing
        fig_num: str | int | float
                - Prefix to the "abc"

        Returns
        -------
        None
        """
        
        n_aux_tier = config.count("a")
        n_signal_tier = config.count("s")
        n_matrix_tier = config.count("m")
        n_tiers = n_aux_tier + n_signal_tier + n_matrix_tier # Number of tiers
        
        # Decide heights of different subplots type
        height = {}
        height["a"] = 0.4 # Aux height
        height["s"] = 2.0 # Signal height
        height["m"] = 4.0 # Matrix height
        cbar_width = 0.01 # For second column (for matrix plots)
        
        # Calculate height ratios for each tier
        for char in config:
            height_ratios = [height[char] for char in config]
            
            # Calculate total fig height
        fig_height = (n_aux_tier * height["a"]) + (n_signal_tier * height["s"]) + (n_matrix_tier * height["m"])
        
        # Create figure and axs based on the config
        fig, axs = plt.subplots(n_tiers, 2, figsize=(fig_width, fig_height), height_ratios=height_ratios, width_ratios=[1, cbar_width])
        
        if axs.ndim == 1:
            axs = np.array([axs]) # This is done otherwise axs[i, 0] does not work
            
        for i, char in enumerate(config): # Loop through each tier and adjust the layout
            if char == "a": # Remove ticks and labels from all the aux subplots
                axs[i, 0].tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
            elif char == "s":
                axs[i, 0].tick_params(bottom=False, labelbottom=False)
            elif char == "m":
                axs[i, 0].tick_params(bottom=False, labelbottom=False)
            
            axs[i, 1].axis("off") # Turn off the column 2, only turn it on when matrix is plotted with colorbar
            
            axs[i, 0].sharex(axs[0, 0]) # Share the x-axis to make all the tiers aligned
            
        # Add tags (1a, 4.1c, ...) to each tier for better referencing in research papers.
        if abc is True:
            for i, char in enumerate(config):
                label = chr(97 + i)  # 97 is ASCII for 'a'
                axs[i, 0].text(-0.06, 0.5, f'{fig_num}{label} $\\rightarrow$', transform=axs[i, 0].transAxes, fontsize=10, va='center', ha='right')
                
                # Turn on the x-label for the last tier
        axs[-1, 0].tick_params(bottom=True, labelbottom=True)
        
        # xlim should be applied on reference subplot, rest all subplots will automatically adjust
        if xlim is not None:
            axs[0, 0].set_xlim(xlim)
            
        fig.subplots_adjust(hspace=0.2, wspace=0.05)
        
        self.type = "tiers"
        self.fig = fig
        self.axs = axs
        
    def grids(self, config, tile_size, remove_ticks, ylim, xlim, abc):
        """
        Generate 2D grid-like canvas based on the configuration.
        
        Parameters
        ----------
        config: tuple[int, int]
            - (n_rows, n_cols)
        tile_size: float
            - Size of each cell in the grid (in inches)
        remove_ticks: bool
            - If True, remove the x- and y-ticks from all tiles.
        ylim: tuple | None
            - (start, end) of x-axis limit.
        xlim: tuple | None
            - (start, end) of y-axis limit.
        abc: bool
            - If True, label each subplot as a, b, c, ...
        """
        
        import matplotlib.pyplot as plt
        import numpy as np
        import string
        
        n_rows, n_cols = config
        
        fig, axs = plt.subplots(
            n_rows, n_cols,
            figsize=(tile_size * n_cols, tile_size * n_rows)
        )
        
        # Flatten axes safely
        axs_flat = np.ravel(np.atleast_1d(axs))
        
        # Remove ticks if requested
        if remove_ticks:
            for ax in axs_flat:
                ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
                
        # Apply limits
        for ax in axs_flat:
            if xlim is not None:
                ax.set_xlim(xlim)
            if ylim is not None:
                ax.set_ylim(ylim)
                
        # Add (a), (b), (c), ... as titles
        if abc:
            labels = list(string.ascii_lowercase)
            for i, ax in enumerate(axs_flat):
                if i < len(labels):
                    ax.set_title(
                        f"({labels[i]})",
                        fontsize=10,
                        loc="center"
                    )
                    
        # Make sure layout leaves space for titles
        plt.tight_layout()
        
        self.type = "grids"
        self.fig = fig
        self.axs = axs
        
    def stacks(self, config, cell_size, overlap, remove_ticks, focus, offset, facecolor, edgecolor):
        """
        Generate 3D stacks like canvas based on the configuration.

        Parameters
        ----------
        config: int
                - Number of tiles
        tile_size: number
                - Size of the tile
        overlap: float
                - Fraction of overlap between consecutive tiles.
        remove_ticks: bool
                - If True, hides all axis ticks and labels for a cleaner stacked appearance.
        focus: int | None
                - Index of the tile to highlight. 
                - The focused tile is offset outward (to the right) by `offset` units.
        offset: float, optional, default=0.25
                - Horizontal displacement for the focused tile. 
                - Determines how far the focused tile "pops out" from the stack.
        facecolor: str
                - Background color for each tile.
        edgecolor: str
                - Color used for the edges of subplot tiles.

        Returns
        -------
        Self
        """
        
        fig = plt.figure(figsize=(cell_size * 2, cell_size * 2))
        axs = []
        
        width, height = 0.8, 0.8
        
        # Base positions (first tile on top, stack grows top-right)
        base_positions = [(0.1 + i * overlap * 0.1, 0.1 + i * overlap * 0.1) for i in range(config)]
        
        # Create all axes first
        for i in range(config):
            left, bottom = base_positions[i]
            ax = fig.add_axes([left, bottom, width, height], facecolor=facecolor, zorder=(config - i))
            ax.patch.set_edgecolor(edgecolor)
            ax.patch.set_linewidth(1.5)
            ax.set_aspect('equal', adjustable='box')
            if remove_ticks:
                ax.set_xticks([])
                ax.set_yticks([])
            axs.append(ax)
            
            # Handle focus highlighting, ghost, and connector
        if focus is not None and 0 <= focus < config:
            left, bottom = base_positions[focus]
            new_left = left + offset
            new_bottom = bottom
            
            # Ghost rectangle (beneath upper layers)
            ghost_rect = Rectangle((left, bottom), width, height, transform=fig.transFigure, facecolor='gray', edgecolor='red', linewidth=1.0, linestyle='-', zorder=(config - focus) - 0.5)
            fig.patches.append(ghost_rect)
            
            # Connector from right edge to new popped tile
            x0 = left + width
            y0 = bottom + height * 0.5
            x1 = new_left
            y1 = new_bottom + height * 0.5
            
            connector = mlines.Line2D([x0, x1], [y0, y1], transform=fig.transFigure, linestyle='--', linewidth=1.0, color='red', zorder=(config - focus) - 0.5)
            fig.lines.append(connector)
            
            # Move focused tile to new position and highlight
            axs[focus].set_position([new_left, new_bottom, width, height])
            axs[focus].patch.set_edgecolor('red')
            axs[focus].patch.set_linewidth(2.5)
            axs[focus].set_zorder(config + 1)
            
        self.type = "stacks"
        self.fig = fig
        self.axs = axs
        
    def single(self):
        
        self.type= "single"
        pass

#============= Fig Class ============
class Fig:
    """
    Provides user-facing APIs to create
    preset canvas (tiers type / grid type)
    to plot 1D array, 2D array, annotation, 
    events.
    """
    
    def __init__(self):
        
        _load_devanagari_font()
        
        self._canvas = _Canvas() # Empty canvas
        self._curr_tile_idx = 0
        self._curr_color_idx = 0 # Choosing color for each stroke of painting
        self._xlim = None # This will be used while plotting annotations as we need to know how much to plot
        
    def _get_curr_tile(self):
        """
        Returns the current tile on which
        painting should be done.
        """
        if self._canvas.type == "tiers":
            curr_tile = self._canvas.axs[self._curr_tile_idx, 0]
            self._curr_tile_idx += 1
        elif self._canvas.type == "grids":
            curr_tile = self._canvas.axs.ravel()[self._curr_tile_idx]
            self._curr_tile_idx += 1
        elif self._canvas.type == "stacks":
            curr_tile = self._canvas.axs[self._curr_tile_idx]
            self._curr_tile_idx += 1
            
        return curr_tile
    
    def _get_cbar_tile(self):
        """
        Returns the tile on which color
        bar should be painted.
        """
        cbar_tile = self._canvas.axs[self._curr_tile_idx - 1, 1]
        
        return cbar_tile
    
    def _get_new_color(self):
        """
        Returns new color for each
        stroke of painting.
        """
        
        colors = plt.cm.tab20.colors
        self._curr_color_idx += 1
        
        return colors[self._curr_color_idx % len(colors)]
    
    def _tier_xlabel(self, xlabel):
        """
        Set shared x-label to the tiles.

        Parameters
        ----------
        xlabel: str | None
            - xlabel for the figure.
        """
        axs = self._canvas.axs
        last_ax = axs[-1, 0] # X-label is added to the last subplot
        if xlabel is not None:
            last_ax.set_xlabel(xlabel)
    
    @classmethod
    def tiers(cls, config, xlim=None, fig_width=16, abc=True, fig_num=""):
        """
        Generates tier-like canvas
        based on the config.

        Parameters
        ----------
        config: str
            - A string combination of "a" for auxilary, "s" for signal, "m" for matrix
            - Eg. "ams", "aa", "a", "sam" etc.
        xlim: tuple | None
            - (start, end) of xlim.
            - Default: None
        fig_width: int
            - Figure width
            - Default: 16
        abc: bool
            - Assign each tier a character for referencing
            - Default: True
        fig_num: str | int | float
            - Prefix to the "abc"
            - Default: ""

        Returns
        -------
        A new Fig object
        """
        
        fig_obj = cls()
        
        fig_obj._xlim = xlim
        fig_obj._canvas.tiers(config, xlim, fig_width, abc, fig_num)
        fig_obj._tier_xlabel("Time (sec)") # Set the xlabel to "Time (sec)"
        
        return fig_obj
    
    @classmethod
    def grids(cls, config, tile_size=2, overlap=1.0, remove_ticks=True, ylim=None, xlim=None, abc=True):
        """
        Generates grid-like canvas
        based on the config.

        Parameters
        ----------
        config: tuple[int, int]
            - (n_rows, n_cols)
            - Eg. (2, 3)
        tile_size: int
            - Size of each cell in the grid
            - Default: 2
        remove_ticks: bool
            - Remove the x-ticks and y-ticks from all the tiles.
            - Default: True
        xlim: tuple
            - (start, end) of xlim.
            - Default: None
        ylim: tuple
            - (start, end) of xlim.
            - Default: None
        abc: bool
            If True, label each subplot as a, b, c, ...

        Returns
        -------
        A new Fig object
        """
        
        fig_obj = cls()
        
        fig_obj._xlim = xlim
        fig_obj._canvas.grids(config, tile_size, remove_ticks, ylim, xlim, abc)
        
        return fig_obj
    
    @classmethod
    def stacks(cls, config, tile_size=1, overlap=0.3, remove_ticks=True, focus=None, offset=4.0):
        """
        Generates stack-like canvas
        based on the config.

        Parameters
        ----------
        config: int
            - Number of tiles
        tile_size: number
            - Size of the tile
            - 
        overlap: float
            - Fraction of overlap between consecutive tiles.
        remove_ticks: bool
            - If True, hides all axis ticks and labels for a cleaner stacked appearance.
        focus: int | None
            - Index of the tile to highlight. 
            - The focused tile is offset outward (to the right) by `offset` units.
        offset: float, optional, default=0.25
            - Horizontal displacement for the focused tile. 
            - Determines how far the focused tile "pops out" from the stack.

        Returns
        -------
        A New fig object.
        """
        
        fig_obj = cls()
        
        fig_obj._canvas.stacks(config, tile_size, overlap, remove_ticks, focus, offset, "white", "black")
        
        return fig_obj
    
    def paint_1d(self, y, x=None, c=None, ls=None, lw=None, m=None, ms=3, label=None, ylabel=None, ylim=None, yticks=None, yticklabels=None, xlabel=None, xticks=None, xticklabels=None, grid=True, same_tile=False):
        """
        Paint 1D array to the current tile.
            
        Parameters
        ----------
        y: np.ndarray
            - Signal y values.
        x: np.ndarray | None
            - Signal x values.
            - Default: None (indices will be used)
        c: str
            - Color of the line.
            - Default: None
        ls: str
            - Linestyle
            - Default: None
        lw: Number
            - Linewidth
            - Default: None
        m: str
            - Marker
            - Default: None
        ms: number
            - Markersize
            - Default: 3
        label: str
            - Label for the plot.
            - Legend will use this.
            - Default: None
        ylabel: str
            - y-label for the plot.
            - Default: None
        ylim: tuple
            - y-lim for the plot.
            - Default: None
        yticks: Arraylike
            - Positions at which to place y-axis ticks.
        yticklabels : list of str, optional
            - Labels corresponding to `yticks`. Must be the same length as `yticks`.
        xlabel: str
            - x-label for the plot.
            - Default: None
        xticks: Arraylike
            - Positions at which to place x-axis ticks.
        xticklabels : list of str, optional
            - Labels corresponding to `xticks`. Must be the same length as `xticks`.
        grid: bool
            - Do you want the grid?
            - Default: True
        same_tile: bool
            - True if you want to paint it in the same tile (meaning the last tile).
            - False

        Returns
        -------
        None
        """
        
        if same_tile is False:
            tile = self._get_curr_tile()
        else:
            self._curr_tile_idx -= 1 # Go to the last tile that was painted
            tile = self._get_curr_tile() # Grab it to paint on it again
            
        if x is None: x = np.arange(y.size)
        if c is None: c = self._get_new_color()
        
        tile.plot(x, y, color=c, linestyle=ls, linewidth=lw, marker=m, markersize=ms, label=label)
        
        if ylabel is not None: 
            tile.set_ylabel(ylabel)
            
        if xlabel is not None:
            if self._canvas.type == "grids":
                tile.set_xlabel(xlabel)
            elif self._canvas.type == "tiers":
                self._tier_xlabel(xlabel)
                
        if ylim is not None: 
            tile.set_ylim(ylim)
            
        if yticks is not None:
            tile.set_yticks(yticks)
            if yticklabels is not None:
                tile.set_yticklabels(yticklabels)
                
        if xticks is not None:
            tile.set_xticks(xticks)
            if xticklabels is not None:
               tile.set_xticklabels(xticklabels)
                
        if grid is True:
            tile.grid(True, linestyle='--', linewidth=0.7, color="lightgray" ,alpha=0.6)
            
    def paint_2d(self, M, y=None, x=None, c="viridis", o="upper", label=None, ylabel=None, ylim=None, yticks=None, yticklabels=None, xlabel=None, xticks=None, xticklabels=None, cbar=True, grid=True, alpha=1, same_tile=False):
        """
        Paint 2D matrix to the current tile.
            
        Parameters
        ----------
        M: np.ndarray
            - Matrix (2D) array
        y: np.ndarray | None
            - y axis values.
        x: np.ndarray | None (indices will be used)
            - x axis values.
            - Default: None (indices will be used)
        c: str
            - cmap for the matrix.
            - Default: None
        o: str
            - origin
            - Default: "lower"
        label: str
            - Label for the plot.
            - Legend will use this.
            - Default: None
        ylabel: str
            - y-label for the plot.
            - Default: None
        ylim: tuple
            - y-lim for the plot.
            - Default: None
        yticks: Arraylike
            - Positions at which to place y-axis ticks.
        yticklabels : list of str, optional
            - Labels corresponding to `yticks`. Must be the same length as `yticks`.
        xlabel: str
            - x-label for the plot.
            - Default: None
        xticks: Arraylike
            - Positions at which to place x-axis ticks.
        xticklabels : list of str, optional
            - Labels corresponding to `xticks`. Must be the same length as `xticks`.
        cbar: bool
            - Show colorbar
            - Default: True
        grid: bool
            - Do you want the grid?
            - Default: True
        alpha: float (0 to 1)
            - Transparency level
            - 1 being opaque and 0 being completely transparent
            - Default: 1
        same_tile: bool
            - True if you want to paint it in the same tile (meaning the last tile).
            - False
        
        Returns
        -------
        None
        """
        
        if same_tile is False:
            tile = self._get_curr_tile()
        else:
            self._curr_tile_idx -= 1 # Go to the last tile that was painted
            tile = self._get_curr_tile() # Grab it to paint on it again
            
        if x is None: x = np.arange(M.shape[1])
        if y is None: y = np.arange(M.shape[0])
        
        def _calculate_extent(x, y, o):
            """
            Calculate x and y axis extent for the 
            2D matrix.
            """
            # Handle spacing safely
            if len(x) > 1:
                dx = x[1] - x[0]
            else:
                dx = 1  # Default spacing for single value
            if len(y) > 1:
                dy = y[1] - y[0]
            else:
                dy = 1  # Default spacing for single value
                
            if o == "lower":
                return  [x[0] - dx / 2, x[-1] + dx / 2, y[0] - dy / 2, y[-1] + dy / 2]
            else:
                return [x[0] - dx / 2, x[-1] + dx / 2, y[-1] + dy / 2, y[0] - dy / 2]
            
        extent = _calculate_extent(x, y, o)
        
        im = tile.imshow(M, aspect="auto", origin=o, cmap=c, extent=extent, alpha=alpha)
        
        if ylabel is not None: tile.set_ylabel(ylabel)
        
        if xlabel is not None:
            if self._canvas.type == "grids":
                tile.set_xlabel(xlabel)
            elif self._canvas.type == "tiers":
                self._tier_xlabel(xlabel)
                
                
        if ylim is not None:
            if o == "lower": tile.set_ylim(ylim)
            elif o == "upper": tile.set_ylim(ylim[::-1])
            
        # Colorbar
        if cbar is True:
            if self._canvas.type == "tiers":
                cbar_tile = self._get_cbar_tile()
                cbar_tile.axis("on")
                cbar = plt.colorbar(im, cax=cbar_tile)
            elif self._canvas.type == "grids":
                cbar = plt.colorbar(im)
            if label is not None: cbar.set_label(label, labelpad=5)
            
        if yticks is not None:
            tile.set_yticks(yticks)
            if yticklabels is not None: tile.set_yticklabels(yticklabels)
            
        if xticks is not None:
            tile.set_xticks(xticks)
            if xticklabels is not None: tile.set_xticklabels(xticklabels)
            
        if grid is True:
            tile.grid(True, linestyle='--', linewidth=0.7, color="lightgray" ,alpha=0.6)
            
    def paint_annotation(self, ann, patterns=None, ylim=(0, 1), text_loc="m", grid=True, same_tile=False):
        """
        Paint annotation to the current tile. 
        Use modusa.load_ann() output.
        
        Parameters
        ----------
        ann : list[tuple[Number, Number, str]] | None
            - A list of annotation spans. Each tuple should be (start, end, label).
            - Default: None (no annotations).
        patterns: list[str]
            - Patterns to group annotations
            - E.g., "*R" or "<tag>*" or ["A*", "*B"]
            - All elements in a group will have same color.
        ylim: tuple[number, number]
            - Y-limit for the annotation.
            - Default: (0, 1)
        text_loc: str
            - Location of text relative to the box. (b for bottom, m for middle, t for top)
            - Default: "m"
        grid: bool
            - Do you want the grid?
            - Default: True
        same_tile: bool
            - True if you want to paint it in the same tile (meaning the last tile).
            - False
        Returns
        -------
        None
        """
        if same_tile is False:
            tile = self._get_curr_tile()
        else:
            self._curr_tile_idx -= 1 # Go to the last tile that was painted
            tile = self._get_curr_tile() # Grab it to paint on it again
            
        xlim = self._xlim
        
        if isinstance(patterns, str): patterns = [patterns]
        ann_copy = ann.copy()
        
        if patterns is not None:
            for i, (start, end, tag) in enumerate(ann_copy):
                group = None
                for j, pattern in enumerate(patterns):
                    if fnmatch.fnmatch(tag, pattern):
                        group = j
                        break
                ann_copy[i] = (start, end, tag, group)
        else:
            for i, (start, end, tag) in enumerate(ann_copy):
                ann_copy[i] = (start, end, tag, None)
                
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        
        # Text Location
        if text_loc in ["b", "bottom", "lower", "l"]: 
            text_yloc = ylim[0] + 0.1 * (ylim[1] - ylim[0])
        elif text_loc in ["t", "top", "u", "upper"]:
            text_yloc = ylim[1] - 0.1 * (ylim[1] - ylim[0])
        else:
            text_yloc = (ylim[1] + ylim[0]) / 2
            
        for i, (start, end, tag, group) in enumerate(ann_copy):
            # We make sure that we only plot annotation that are within the x range of the current view
            if xlim is not None:
                if start >= xlim[1] or end <= xlim[0]:
                    continue
                
                # Clip boundaries to xlim
                start = max(start, xlim[0])
                end = min(end, xlim[1])
                
                
                if group is not None:
                    box_color = colors[group]
                else:
                    box_color = "lightgray"
                    
                width = end - start
                rect = Rectangle((start, ylim[0]), width, ylim[1] - ylim[0], facecolor=box_color, edgecolor="black", alpha=0.7)
                tile.add_patch(rect)
                
                text_obj = tile.text(
                    (start + end) / 2, text_yloc, tag,
                    ha='center', va='center',
                    fontsize=9, color="black", zorder=10, clip_on=True
                )
                
                text_obj.set_clip_path(rect)
            else:
                if group is not None:
                    box_color = colors[group]
                else:
                    box_color = "lightgray"
                    
                width = end - start
                rect = Rectangle((start, ylim[0]), width, ylim[1] - ylim[0], facecolor=box_color, edgecolor="black", alpha=0.7)
                tile.add_patch(rect)
                
                text_obj = tile.text(
                    (start + end) / 2, text_yloc, tag,
                    ha='center', va='center',
                    fontsize=10, color="black", zorder=10, clip_on=True
                )
                
                text_obj.set_clip_path(rect)
                
        if grid is True:
            tile.grid(True, linestyle='--', linewidth=0.7, color="lightgray" ,alpha=0.6)
            
    def paint_events(self, events, c=None, ls=None, lw=None, label=None, grid=True, same_tile=False):
        """
        Paint events to the current tile.
        
        Parameters
        ----------
        events: np.ndarray
            - All the event marker values.
        c: str
            - Color of the event marker.
            - Default: "k"
        ls: str
            - Line style.
            - Default: "-"
        lw: float
            - Linewidth.
            - Default: 1.5
        label: str
            - Label for the event type.
            - This will appear in the legend.
            - Default: None
        grid: bool
            - Do you want the grid?
            - Default: True
        same_tile: bool
            - True if you want to paint it in the same tile (meaning the last tile).
            - False

        Returns
        -------
        None
        """
        
        if same_tile is False:
            tile = self._get_curr_tile()
        else:
            self._curr_tile_idx -= 1 # Go to the last tile that was painted
            tile = self._get_curr_tile() # Grab it to paint on it again
            
        if c is None: c = self._get_new_color()
        
        xlim = self._xlim
        
        for i, event in enumerate(events):
            if xlim is not None:
                if xlim[0] <= event <= xlim[1]:
                    if i == 0: # Label should be set only once for all the events
                        tile.axvline(x=event, color=c, linestyle=ls, linewidth=lw, label=label)
                    else:
                        tile.axvline(x=event, color=c, linestyle=ls, linewidth=lw)
            else:
                if i == 0: # Label should be set only once for all the events
                    tile.axvline(x=event, color=c, linestyle=ls, linewidth=lw, label=label)
                else:
                    tile.axvline(x=event, color=c, linestyle=ls, linewidth=lw)
                    
        if grid is True:
            tile.grid(True, linestyle='--', linewidth=0.7, color="lightgray" ,alpha=0.6)
            
    def paint_arrows(self, xys, labels, text_offset=(0, 0), c="r", fontsize=12, same_tile=True):
        """
        Paint multiple arrows pointing to specific points with boxed labels at the tails
        in the last tile.
    
        Parameters
        ----------
        xys : list[tuple[float, float]] | tuple[float, float]
            - List of target points (x, y) for the arrow heads.
        labels : list[str] | str
            - List of text labels at the arrow tails.
            - If str, the same label is used for all points.
        text_offset : tuple[float, float] | list[tuple[float, float]]
            - Offset(s) (dx, dy) for label positions from arrow tails.
            - If single tuple, same offset is applied to all.
        c : str | list[str]
            - Color(s) for arrow and text.
            - If str, same color is applied to all.
        fontsize : int | list[int]
            - Font size(s) of the label text.
            - If int, same size is applied to all.
        same_tile: bool
            - True if you want to paint it in the same tile (meaning the last tile).
            - Default: True
    
        Returns
        -------
        None
        """
        
        if same_tile is False:
            tile = self._get_curr_tile()
        else:
            self._curr_tile_idx -= 1 # Go to the last tile that was painted
            tile = self._get_curr_tile() # Grab it to paint on it again
            
        # Normalize single values into lists
        if isinstance(xys, tuple):
            xys = [xys]
        n = len(xys)
        if isinstance(labels, str):
            labels = [labels] * n
        if isinstance(text_offset, tuple):
            text_offset = [text_offset] * n
        if isinstance(c, str):
            c = [c] * n
        if isinstance(fontsize, int):
            fontsize = [fontsize] * n
            
        for (xy, label, offset, color, fs) in zip(xys, labels, text_offset, c, fontsize):
            arrowprops = dict(arrowstyle="->", color=color, lw=2)
            bbox = dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.2)
            
            text_x, text_y = xy[0] + offset[0], xy[1] + offset[1]
            
            tile.annotate(
                label,
                xy=xy, xycoords="data",
                xytext=(text_x, text_y), textcoords="data",
                arrowprops=arrowprops,
                fontsize=fs,
                color=color,
                ha="center", va="center",
                bbox=bbox
            )
            
    def legend(self, ypos=1.0, grouped=True):
        """
        Add legend(s) to the figure.
    
        Parameters
        ----------
        ypos : float, optional
            Vertical position of the figure-level legend (only if grouped=True).
            > 1 pushes it higher, < 1 pushes it lower. Default is 1.0.
        grouped : bool, optional
            If True, combine all legend entries into one figure-level legend.
            If False, add individual legends to each subplot.
    
        Returns
        -------
        None
        """
        fig = self._canvas.fig
        axs = np.ravel(self._canvas.axs)  # works for 1D or 2D grids
        
        if grouped:
            # --- Combine all handles and labels ---
            all_handles, all_labels = [], []
            for ax in axs:
                handles, labels = ax.get_legend_handles_labels()
                all_handles.extend(handles)
                all_labels.extend(labels)
                
            # --- Remove duplicates while preserving order ---
            unique = dict(zip(all_labels, all_handles))
            fig.legend(
                unique.values(),
                unique.keys(),
                loc="upper right",
                bbox_to_anchor=(1, ypos),
                ncol=min(len(axs), 4),  # up to 4 columns or as many as tiles
                frameon=True,
                bbox_transform=fig.transFigure
            )
            
        else:
            # --- Individual legends per subplot ---
            for ax in axs:
                handles, labels = ax.get_legend_handles_labels()
                if handles:
                    ax.legend(handles, labels, loc="upper right", frameon=True)
                    
    def title(self, title=None, s=13):
        """
        Set the title of the canvas.

        Parameters
        ----------
        title: str | None
            - Title of the figure.
            - Default: None
        s: Number
            - Font size.
            - Default: None
        """
        axs = self._canvas.axs
        first_ax = axs[0, 0] # Title is added to the top subplot (ref subplot)
        
        if title is not None:
            first_ax.set_title(title, pad=10, size=s)

#========= Animation Class ==========
class Animation:
    """
    A context-managed animation builder.
    
    Parameters
    ----------
    path : str
        Output file path (e.g. "wave.gif")
    fps: int
        - Frames per second of the output animation
        - Default: 8
    pad: float
        - Padding (inches) around each frame to give consistent breathing space
        - Default: 0.4
    facecolor: str
        - Background color for each frame
        - Default: "white"
    """
    def __init__(self, path, fps=8, pad=0.4, facecolor='white', loop=True):
        self._path = path
        self._fps = fps
        self._pad = pad
        self._facecolor = facecolor
        self._loop = loop
        self._frames = []
        
    def __enter__(self):
        return self
    
    def capture_frame(self, fig):
        """Capture a matplotlib figure with consistent padding."""
        fig = fig._canvas.fig
        buf = BytesIO()
        fig.savefig(
            buf,
            format="png",
            bbox_inches="tight",
            pad_inches=self._pad,
            facecolor=self._facecolor,
        )
        buf.seek(0)
        img = imageio.imread(buf)
        self._frames.append(img)
        buf.close()
        plt.close(fig)
        
    def _save(self):
        """Save the collected frames as a GIF (uniform shape)."""
        if not self._frames:
            raise ValueError("No frames captured to save.")
            
        # Match all frames to smallest common shape
        min_h = min(f.shape[0] for f in self._frames)
        min_w = min(f.shape[1] for f in self._frames)
        resized_frames = [f[:min_h, :min_w, ...] for f in self._frames]
        
        # loop=0 means infinite loop, loop=1 means play once
        imageio.mimsave(
            self._path,
            resized_frames,
            fps=self._fps,
            loop=0 if self._loop else 1
        )
        self._saved = True
        
        print(f"Animation saved to {self._path} ({len(self._frames)} frames).")
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()
        with open(self._path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
    
        # Create HTML img tag — nbconvert captures this correctly
        html = f'<img src="data:image/gif;base64,{b64}" loop="infinite" />'
    
        # Display works both in live notebook and in exported HTML
        display(HTML(html))

        
#======= Hill Plot ========
def hill_plot(*args, labels=None, xlabel=None, ylabel=None, title=None, widths=0.7, bw_method=0.3, jitter_amount=0.1, side='upper', show_stats=True, ax=None):
    """
    A plot to see distribution of different groups
    along with statistical markers.
    
    Parameters
    ----------
    *args: array-like
            - Data arrays for each group.
    labels: list of str, optional
            - Labels for each group (y-axis).
    ylabel: str, optional
            Label for y-axis.
    xlabel: str, optional
            Label for x-axis.
    title: str, optional
            Plot title.
    widths: float, optional
            Width of violins.
    bw_method: float, optional
            Bandwidth method for KDE.
    jitter_amount: float, optional
            Amount of vertical jitter for strip points.
    side: str, 'upper' or 'lower'
            Which half of the violin to draw (upper or lower relative to y-axis).
    show_stats: bool, optional
            Whether to show mean and median markers.
    ax: matplotlib axes, optional
            Axes to plot on.
    """
    
    plt.style.use("default") # Not supporting dark mode
    plt.rcParams['font.family'] = "DejaVu Sans" # Devnagari not needed for this.
    
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, len(args) * 1.5))
        created_fig = True
        
    n = len(args)
    
    # Default labels/colors
    if labels is None:
        labels = [f"Group {i}" for i in range(1, n+1)]
    if isinstance(labels, str):
        labels = [labels]
        
    colors = plt.cm.tab10.colors
    if len(colors) < n:
        colors = [colors[i % len(colors)] for i in range(n)] # Repeat colors
        
        # --- Half-violin ---
    parts = ax.violinplot(args, vert=False, showmeans=False, showmedians=False, widths=widths, bw_method=bw_method)
    
    # Remove the default bar lines from violin plot
    for key in ["cbars", "cmins", "cmaxes", "cmedians"]:
        if key in parts:
            parts[key].set_visible(False)
            
            # Clip violin bodies to show only upper or lower half
    for i, pc in enumerate(parts['bodies']):
        verts = pc.get_paths()[0].vertices
        y_center = i + 1  # Center y-position for this violin
        
        if side == "upper":
            verts[:, 1] = np.maximum(verts[:, 1], y_center)
        else:  # 'lower'
            verts[:, 1] = np.minimum(verts[:, 1], y_center)
        
        pc.set_facecolor(colors[i])
        pc.set_edgecolor(colors[i])
        pc.set_linewidth(1.5)
        pc.set_alpha(0.3)
        
        # --- Strip points with jitter ---
    for i, x in enumerate(args, start=1):
        x = np.array(x)
        jitter = (np.random.rand(len(x)) - 0.5) * jitter_amount
        y_positions = np.full(len(x), i) + jitter
        ax.scatter(x, y_positions, color=colors[i-1], alpha=0.6, s=25, edgecolor="white", linewidth=0.8, zorder=2)
        
        # --- Statistical markers on violin distribution curve ---
    if show_stats:
        for i, (pc, x) in enumerate(zip(parts['bodies'], args), start=1):
            x = np.array(x)
            median_val = np.median(x)
            mean_val = np.mean(x)
            std_val = np.std(x)
            
            # Get the violin curve vertices
            verts = pc.get_paths()[0].vertices
            
            # Find y-position on violin curve for median
            median_mask = np.abs(verts[:, 0] - median_val) < (np.ptp(x) * 0.01)
            if median_mask.any():
                median_y = np.max(verts[median_mask, 1]) if side == "upper" else np.min(verts[median_mask, 1])
            else:
                median_y = i + widths/2 if side == "upper" else i - widths/2
                
                # Find y-position on violin curve for mean
            mean_mask = np.abs(verts[:, 0] - mean_val) < (np.ptp(x) * 0.01)
            if mean_mask.any():
                mean_y = np.max(verts[mean_mask, 1]) if side == "upper" else np.min(verts[mean_mask, 1])
            else:
                mean_y = i + widths/2 if side == "upper" else i - widths/2
                
                # Triangle offset from curve
            triangle_offset = 0.05
            
            # Mean marker - triangle below curve pointing up
            ax.scatter(mean_val, mean_y - triangle_offset, marker="^", s=30, 
                facecolor=colors[i-1], edgecolor="black", 
                linewidth=0.5, zorder=6,
                label="Mean" if i == 1 else "")
            
            # Mean value text - below the triangle
            ax.text(mean_val, mean_y - triangle_offset - 0.07, f"mean: {mean_val:.2f} ± {std_val:.2f}", ha="center", va="top", fontsize=8, color="black", zorder=7)
            
            # Median marker - triangle above curve pointing down
            ax.scatter(median_val, median_y + triangle_offset, marker="v", s=30, 
                facecolor=colors[i-1], edgecolor="black", 
                linewidth=0.5, zorder=6,
                label="Median" if i == 1 else "")
            
            # Median value text - above the triangle
            ax.text(median_val, median_y + triangle_offset + 0.07, f"median: {median_val:.2f}", ha="center", va="bottom", fontsize=8, color="black", zorder=7)
            
            # --- Labels & formatting ---
    ax.set_yticks(range(1, n + 1))
    ax.set_yticklabels(labels, fontsize=9)
    ax.tick_params(axis='x', labelsize=9)
    
    if side == "lower":
        ax.set_ylim(0.2, n + 0.5)
    else:
        ax.set_ylim(0.5, n + 0.5) 
        
        # Style improvements
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle="--", linewidth=0.5)
    
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    if title:
        ax.set_title(title, fontsize=10, pad=20)
        
    plt.tight_layout()
    plt.close()
    return fig


# ======== Single Plot ===========
def plot(*args):
    """
    To create 1D/2D plot for immediate
    inspection.

    Parameters
    ----------
    *args: ndarray
        - Arrays to be plotted.
    """
    n = len(args)
    
    if n < 1:
        raise ValueError("Need atleast 1 positional argument")
        
        ## 1D Array
    if args[0].ndim == 1:
        if n > 1: # User also passed the xs
            fig = Fig("s").add_signal(args[0], args[1])
        else:
            fig = Fig("s").add_signal(args[0])
            
            ## 2D Array
    if args[0].ndim == 2:
        if n == 1:
            fig = Fig("m").add_matrix(args[0])
        elif n == 2: # User also passed the xs
            fig = Fig("m").add_matrix(args[0], args[1])
        elif n == 3:
            fig = Fig("m").add_matrix(args[0], args[1], args[2])
            
    return fig



