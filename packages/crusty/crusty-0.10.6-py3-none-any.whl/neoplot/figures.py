
from dataclasses import dataclass, field
import matplotlib as mpl
import matplotlib.transforms as mtr
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import cartopy.crs as ccrs
from matplotlib.gridspec import GridSpec
import matplotlib.axes as maxes
from mpl_toolkits.axes_grid1 import make_axes_locatable
import string
import os

from pathlib import Path, PosixPath
from cartopy.mpl.geoaxes import GeoAxes
from typing import Union, List, Literal

# Hier kann man viel mehr zusammenfassen, da in den
# sub-classen viel wiederholt wird

@dataclass(kw_only = True)
class fig_001:

    fy: float = 6.7
    fx: float = 6.7

    dpi: int = 300
    font_color: str = 'dimgray'
    font_dir: Path = Path('/p/scratch/cjibg31/jibg3105/projects/crusty/src/neoplot/fonts/')
    font: str = 'Montserrat'
    constrained: bool = True
    axs: list[GeoAxes] = field(default_factory = list)

    def create(self):
        
        font_files = fm.findSystemFonts(fontpaths = [self.font_dir])
    
        for font_file in font_files:
            fm.fontManager.addfont(font_file)

        mpl.rcParams['font.family'] = self.font
        mpl.rcParams['xtick.color'] = self.font_color
        mpl.rcParams['ytick.color'] = self.font_color

        fig_ = plt.figure(figsize = (self.fx, self.fy), 
                          constrained_layout = self.constrained,
                          dpi = self.dpi)
        
        self.fig = fig_
        
        return self
    
    def annotation(self, 
                   x : float = 0.05, 
                   y : float = 1.05, 
                   fs: float = 12.0):

        abc = string.ascii_lowercase
    
        list_abc = list(abc)

        for iax, ax in enumerate(self.axs):

            ax.text(x, y, list_abc[iax] + ')', 
                    fontsize = fs,
                    transform = ax.transAxes, 
                    va = 'bottom', 
                    ha = 'center')

    def save(self, 
             path: os.PathLike,
             fformat: str = 'png'):

        self.fig.savefig(f'{path}.{fformat}',
                         dpi = self.dpi,
                         bbox_inches = 'tight')
        
        plt.close()

        

@dataclass(kw_only = True)
class single_001(fig_001):

    color_bar: None | list[str] = None
    projection: mtr.Transform | ccrs.Projection | \
                None | Literal['EU3'] = None
    frame: bool = False


    def create(self):

        super().create()

        nrows = 1
        ncols = 1
        axs = []

        if self.projection == 'EU3':
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                           semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                   pole_latitude = rotnpole_lat,
                                   globe = globe)
            
            self.projection = self.rp


        gs = GridSpec(figure = self.fig, 
                      ncols = ncols, 
                      nrows = nrows)

        axs.append(self.fig.add_subplot(gs[0, 0], 
                                        projection = self.projection, 
                                        frameon = self.frame))

        
        self.axs = axs

        return self

    


@dataclass(kw_only = True)
class triple_001(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    def create(self):

        super().create()

        axs = []

        nrows = 1
        ncols = 3

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,)

        for iax in range(ncols):

            axs.append(self.fig.add_subplot(gs[0, iax], 
                                            projection = self.active_proj[iax], 
                                            frameon = self.frame))

        self.axs = axs

        return self


@dataclass(kw_only = True)      
class double_001(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False


    def create(self):

        super().create()

        axs = []

        nrows = 1
        ncols = 2

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols)

        for iax in range(ncols):

            axs.append(self.fig.add_subplot(gs[0, iax], 
                                            projection = self.active_proj[iax], 
                                            frameon = self.frame))

        self.axs = axs

        return self

@dataclass(kw_only = True)      
class double_001_vert(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    def create(self):

        super().create()

        axs = []

        nrows = 2
        ncols = 1

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      hspace = 0.2)

        for iax in range(nrows):

            axs.append(self.fig.add_subplot(gs[iax, 0], 
                                            projection = self.active_proj[iax], 
                                            frameon = self.frame))

        self.axs = axs

        return self
       
            
@dataclass(kw_only = True)
class quatro_001(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        axs = []

        nrows = 2
        ncols = 2

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[1, 0], gs[1, 1]]

        for iax, ax in enumerate(positions):

            axs.append(self.fig.add_subplot(ax, 
                                            projection = self.active_proj[iax], 
                                            frameon = self.frame))

        self.axs = axs

        return self
        

@dataclass(kw_only = True)
class twoxfour(fig_001):

    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 2
        ncols = 4

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[0, 2], gs[0, 3],
                     gs[1, 0], gs[1, 1], gs[1, 2], gs[1, 3],]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self

@dataclass(kw_only = True)
class threexthree(fig_001):

    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 3
        ncols = 4

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[0, 2],
                     gs[1, 0], gs[1, 1], gs[1, 2],
                     gs[2, 0], gs[2, 1], gs[2, 2],]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self
    


@dataclass(kw_only = True)
class threexfour(fig_001):

    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 3
        ncols = 4

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[0, 2], gs[0, 3],
                     gs[1, 0], gs[1, 1], gs[1, 2], gs[1, 3],
                     gs[2, 0], gs[2, 1], gs[2, 2], gs[2, 3],]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self
    

@dataclass(kw_only = True)
class fourxtwo(fig_001):

    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 4
        ncols = 2

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], 
                     gs[1, 0], gs[1, 1],
                     gs[2, 0], gs[2, 1], 
                     gs[3, 0], gs[3, 1],]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self

@dataclass(kw_only = True)
class fivexthree(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 5
        ncols = 3

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[0, 2],
                     gs[1, 0], gs[1, 1], gs[1, 2],
                     gs[2, 0], gs[2, 1], gs[2, 2],
                     gs[3, 0], gs[3, 1], gs[3, 2],
                     gs[4, 0], gs[4, 1], gs[4, 2]]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self
    


@dataclass(kw_only = True)
class fivexfour(fig_001):
    
    projection: List[Union[mtr.Transform, ccrs.Projection, Literal['EU3'], None]] | \
                    mtr.Transform | ccrs.Projection | Literal['EU3'] | None = None
    frame: bool = False

    wspace: float = 0.1
    hspace: float = 0.05

    def create(self):

        super().create()

        nrows = 5
        ncols = 4

        if not isinstance(self.projection, list): 
            
            self.projection = [self.projection for i in range(ncols*nrows)]

        if 'EU3' in self.projection:
    
            rotnpole_lat: float = 39.25 
            rotnpole_lon: float = -162.0

            semmj_axis: None | int = 6370000
            semmn_axis: None | int = 6370000 

            globe = ccrs.Globe(semimajor_axis = semmj_axis,
                               semiminor_axis = semmn_axis)

            self.rp = ccrs.RotatedPole(pole_longitude = rotnpole_lon,
                                       pole_latitude = rotnpole_lat,
                                       globe = globe)

        
            self.active_proj = [self.rp if p == 'EU3' else p 
                                for p in self.projection]
            
        else:
            self.active_proj = self.projection

        gs = GridSpec(figure = self.fig, 
                      nrows = nrows,
                      ncols = ncols,
                      wspace = self.wspace,
                      hspace = self.hspace)
        
        positions = [gs[0, 0], gs[0, 1], gs[0, 2], gs[0, 3],
                     gs[1, 0], gs[1, 1], gs[1, 2], gs[1, 3],
                     gs[2, 0], gs[2, 1], gs[2, 2], gs[2, 3],
                     gs[3, 0], gs[3, 1], gs[3, 2], gs[3, 3],
                     gs[4, 0], gs[4, 1], gs[4, 2], gs[4, 3]]
        
        self.positions = positions

        for iax, ax in enumerate(positions):

            self.axs.append(self.fig.add_subplot(ax, 
                                        projection = self.active_proj[iax], 
                                        frameon = self.frame))

        return self