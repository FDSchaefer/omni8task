import numpy as np
import matplotlib.pyplot as plt


def Scroller(X):

    MAX = max(np.concatenate(X,axis=None))

    class IndexTracker(object):
        def __init__(self, ax, X):
            self.ax = ax
            ax.set_title('use scroll wheel to navigate images')

            self.X = X
            rows, cols, self.slices = X.shape
            self.ind = self.slices//2

            self.im = ax.imshow(self.X[:,:, self.ind], vmax=MAX,aspect = 'equal')
            self.update()

        def onscroll(self, event):
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.update()

        def update(self):
            self.im.set_data(self.X[:, :, self.ind])
            ax.set_ylabel('slice %s' % self.ind)
            self.im.axes.figure.canvas.draw()


    fig, ax = plt.subplots(1, 1)

    tracker = IndexTracker(ax, X)

    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)

    plt.show()


def ScrollerMulti(X,num,name):

    MAX = max(np.concatenate(X,axis=None))

    class IndexTracker(object):
        def __init__(self, ax, X, num,name):
            
            self.ax = ax
            self.X = X
            self.im = self.ax
            for i in range(num):         
                ax[i].set_title(name[i])

                rows, cols, self.slices = X[i].shape
                self.ind = self.slices//2

                self.im[i] = ax[i].imshow(self.X[i][:,:, self.ind], vmax=MAX, aspect = 'equal')
            self.update()

        def onscroll(self, event):
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.update()

        def update(self):
            for i in range(num):
                self.im[i].set_data(self.X[i][:, :, self.ind])
                self.im[i].axes.set_ylabel('slice %s' % self.ind)

            for i in range(num):    #To allow for pause and avoid stutter
                self.im[i].axes.figure.canvas.draw()


    fig, ax = plt.subplots(1, num)

    tracker = IndexTracker(ax, X, num,name)

    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)

    plt.show()


def ScrollerCheckerboard(X1, X2, name1="Image 1", name2="Image 2", checker_size=32):
    """
    Display two images with checkerboard overlay for comparison.
    
    Args:
        X1: First 3D image array
        X2: Second 3D image array (must match X1 shape)
        name1: Name of first image
        name2: Name of second image
        checker_size: Size of checkerboard squares in pixels
    
    Controls:
        Scroll: Navigate through slices
        Key 'c': Toggle checkerboard on/off
        Key '1': Show only image 1
        Key '2': Show only image 2
        Key 'b': Show both (checkerboard)
        Key '+': Increase checker size
        Key '-': Decrease checker size
    """
    if X1.shape != X2.shape:
        raise ValueError(f"Image shapes must match: {X1.shape} != {X2.shape}")
    
    MAX = max(np.max(X1), np.max(X2))
    
    class IndexTracker(object):
        def __init__(self, ax, X1, X2, name1, name2, checker_size):
            self.ax = ax
            self.X1 = X1
            self.X2 = X2
            self.name1 = name1
            self.name2 = name2
            self.checker_size = checker_size
            
            rows, cols, self.slices = X1.shape
            self.ind = self.slices // 2
            self.mode = 'checkerboard'  # 'checkerboard', 'image1', 'image2'
            
            # Create checkerboard mask
            self.update_checkerboard_mask()
            
            # Display
            self.im = ax.imshow(self.get_display_slice(), vmax=MAX, aspect='equal', cmap='gray')
            self.update_title()
            self.update()
        
        def update_checkerboard_mask(self):
            """Create checkerboard pattern mask."""
            rows, cols, _ = self.X1.shape
            self.mask = np.zeros((rows, cols), dtype=bool)
            
            for i in range(0, rows, self.checker_size):
                for j in range(0, cols, self.checker_size):
                    # Alternate checkerboard pattern
                    if ((i // self.checker_size) + (j // self.checker_size)) % 2 == 0:
                        i_end = min(i + self.checker_size, rows)
                        j_end = min(j + self.checker_size, cols)
                        self.mask[i:i_end, j:j_end] = True
        
        def get_display_slice(self):
            """Get the slice to display based on current mode."""
            slice1 = self.X1[:, :, self.ind]
            slice2 = self.X2[:, :, self.ind]
            
            if self.mode == 'image1':
                return slice1
            elif self.mode == 'image2':
                return slice2
            else:  # checkerboard
                display = slice1.copy()
                display[self.mask] = slice2[self.mask]
                return display
        
        def update_title(self):
            """Update plot title with current mode and controls."""
            if self.mode == 'checkerboard':
                mode_str = f"Checkerboard (size={self.checker_size})"
            elif self.mode == 'image1':
                mode_str = f"Only: {self.name1}"
            else:
                mode_str = f"Only: {self.name2}"
            
            self.ax.set_title(
                f'{mode_str} | Keys: c=toggle, 1/2=single, b=both, +/-=size'
            )
        
        def onscroll(self, event):
            """Handle scroll events for slice navigation."""
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.update()
        
        def onkey(self, event):
            """Handle keyboard events for mode switching."""
            if event.key == 'c' or event.key == 'b':
                # Toggle checkerboard
                self.mode = 'checkerboard'
                self.update()
            elif event.key == '1':
                # Show only image 1
                self.mode = 'image1'
                self.update()
            elif event.key == '2':
                # Show only image 2
                self.mode = 'image2'
                self.update()
            elif event.key == '+' or event.key == '=':
                # Increase checker size
                self.checker_size = min(self.checker_size * 2, 128)
                self.update_checkerboard_mask()
                if self.mode == 'checkerboard':
                    self.update()
            elif event.key == '-' or event.key == '_':
                # Decrease checker size
                self.checker_size = max(self.checker_size // 2, 4)
                self.update_checkerboard_mask()
                if self.mode == 'checkerboard':
                    self.update()
        
        def update(self):
            """Update the display."""
            self.im.set_data(self.get_display_slice())
            self.ax.set_ylabel(f'Slice {self.ind}/{self.slices-1}')
            self.update_title()
            self.im.axes.figure.canvas.draw()
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Create tracker
    tracker = IndexTracker(ax, X1, X2, name1, name2, checker_size)
    
    # Connect events
    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    fig.canvas.mpl_connect('key_press_event', tracker.onkey)
    
    plt.show()


def ScrollerDifference(X1, X2, name1="Image 1", name2="Image 2"):
    """
    Display two images side-by-side with difference map.
    
    Args:
        X1: First 3D image array
        X2: Second 3D image array (must match X1 shape)
        name1: Name of first image
        name2: Name of second image
    
    Controls:
        Scroll: Navigate through slices
    """
    if X1.shape != X2.shape:
        raise ValueError(f"Image shapes must match: {X1.shape} != {X2.shape}")
    
    MAX = max(np.max(X1), np.max(X2))
    
    class IndexTracker(object):
        def __init__(self, axes, X1, X2, name1, name2):
            self.axes = axes
            self.X1 = X1
            self.X2 = X2
            
            rows, cols, self.slices = X1.shape
            self.ind = self.slices // 2
            
            # Setup subplots
            axes[0].set_title(name1)
            axes[1].set_title(name2)
            axes[2].set_title('Difference (X1 - X2)')
            
            # Create images
            self.im1 = axes[0].imshow(
                self.X1[:, :, self.ind], 
                vmax=MAX, 
                aspect='equal', 
                cmap='gray'
            )
            self.im2 = axes[1].imshow(
                self.X2[:, :, self.ind], 
                vmax=MAX, 
                aspect='equal', 
                cmap='gray'
            )
            
            # Difference image
            diff = self.X1[:, :, self.ind] - self.X2[:, :, self.ind]
            diff_max = np.max(np.abs(diff))
            self.im_diff = axes[2].imshow(
                diff, 
                vmin=-diff_max, 
                vmax=diff_max,
                aspect='equal', 
                cmap='RdBu_r'
            )
            
            # Add colorbar to difference
            plt.colorbar(self.im_diff, ax=axes[2])
            
            self.update()
        
        def onscroll(self, event):
            """Handle scroll events."""
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.update()
        
        def update(self):
            """Update the display."""
            slice1 = self.X1[:, :, self.ind]
            slice2 = self.X2[:, :, self.ind]
            diff = slice1 - slice2
            
            self.im1.set_data(slice1)
            self.im2.set_data(slice2)
            self.im_diff.set_data(diff)
            
            # Update diff colorbar limits
            diff_max = np.max(np.abs(diff))
            self.im_diff.set_clim(-diff_max, diff_max)
            
            # Update labels
            for i, ax in enumerate(self.axes):
                ax.set_ylabel(f'Slice {self.ind}/{self.slices-1}')
            
            self.im1.axes.figure.canvas.draw()
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Create tracker
    tracker = IndexTracker(axes, X1, X2, name1, name2)
    
    # Connect scroll event
    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    
    plt.tight_layout()
    plt.show()


def ScrollerOverlay(X1, X2, name1="Image 1", name2="Image 2", alpha=0.5):
    """
    Display two images as a blended overlay with adjustable transparency.
    
    Args:
        X1: First 3D image array (shown in red channel)
        X2: Second 3D image array (shown in green channel)
        name1: Name of first image
        name2: Name of second image
        alpha: Initial blend ratio (0=only X1, 1=only X2, 0.5=equal blend)
    
    Controls:
        Scroll: Navigate through slices
        Left/Right arrow: Adjust blend (alpha)
    """
    if X1.shape != X2.shape:
        raise ValueError(f"Image shapes must match: {X1.shape} != {X2.shape}")
    
    class IndexTracker(object):
        def __init__(self, ax, X1, X2, name1, name2, alpha):
            self.ax = ax
            self.X1 = X1
            self.X2 = X2
            self.name1 = name1
            self.name2 = name2
            self.alpha = alpha
            
            rows, cols, self.slices = X1.shape
            self.ind = self.slices // 2
            
            # Create RGB overlay
            self.im = ax.imshow(self.get_overlay(), aspect='equal')
            self.update_title()
            self.update()
        
        def get_overlay(self):
            """Create RGB overlay of two images."""
            slice1 = self.X1[:, :, self.ind]
            slice2 = self.X2[:, :, self.ind]
            
            # Normalize to 0-1
            s1_norm = (slice1 - np.min(slice1)) / (np.max(slice1) - np.min(slice1) + 1e-10)
            s2_norm = (slice2 - np.min(slice2)) / (np.max(slice2) - np.min(slice2) + 1e-10)
            
            # Create RGB: Red=X1, Green=X2, overlap=yellow
            rgb = np.zeros((slice1.shape[0], slice1.shape[1], 3))
            rgb[:, :, 0] = s1_norm * (1 - self.alpha) + s2_norm * self.alpha  # Red + blend
            rgb[:, :, 1] = s2_norm * self.alpha + s1_norm * (1 - self.alpha)  # Green + blend
            rgb[:, :, 2] = 0  # Blue channel unused
            
            return rgb
        
        def update_title(self):
            """Update title with current alpha."""
            self.ax.set_title(
                f'Overlay: {self.name1} ↔ {self.name2} | '
                f'Alpha={self.alpha:.2f} | Use ← → to adjust'
            )
        
        def onscroll(self, event):
            """Handle scroll events."""
            if event.button == 'up':
                self.ind = (self.ind + 1) % self.slices
            else:
                self.ind = (self.ind - 1) % self.slices
            self.update()
        
        def onkey(self, event):
            """Handle keyboard events for alpha adjustment."""
            if event.key == 'right':
                self.alpha = min(self.alpha + 0.1, 1.0)
                self.update()
            elif event.key == 'left':
                self.alpha = max(self.alpha - 0.1, 0.0)
                self.update()
        
        def update(self):
            """Update the display."""
            self.im.set_data(self.get_overlay())
            self.ax.set_ylabel(f'Slice {self.ind}/{self.slices-1}')
            self.update_title()
            self.im.axes.figure.canvas.draw()
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Create tracker
    tracker = IndexTracker(ax, X1, X2, name1, name2, alpha)
    
    # Connect events
    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    fig.canvas.mpl_connect('key_press_event', tracker.onkey)
    
    plt.show()


print('Debug')