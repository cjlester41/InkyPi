document.addEventListener('DOMContentLoaded', function() {
    // Select all image containers instead of just the first one
    const containers = document.querySelectorAll('.image-container');
    let modalOverlay = null;
    let modalImg = null;
    let observer = null;
    let activeContainer = null; // Track which specific container is currently zoomed
    
    if (containers.length === 0) return;

    // Loop through every container found (Display 1, Display 2, etc.)
    containers.forEach(imageContainer => {
        const img = imageContainer.querySelector('img');
        if (!img) return;

        // Attach the click event to each image
        img.addEventListener('click', function(e) {
            e.stopPropagation();
            
            activeContainer = imageContainer;
            
            // Create the zoom overlay
            modalOverlay = document.createElement('div');
            modalOverlay.className = 'image-modal-overlay';
            
            modalImg = document.createElement('img');
            modalImg.src = img.src;
            modalOverlay.appendChild(modalImg);
            
            document.body.appendChild(modalOverlay);
            imageContainer.classList.add('maximized');
            document.body.style.overflow = 'hidden';
            
            // Set up a MutationObserver for this specific image
            // This ensures the zoomed view updates live if the display refreshes
            observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.attributeName === 'src' && modalImg) {
                        modalImg.src = img.src;
                    }
                });
            });
            
            observer.observe(img, { attributes: true, attributeFilter: ['src'] });
        });
    });

    // Handle clicking outside the image to close the zoom
    document.addEventListener('click', function(e) {
        if (activeContainer && activeContainer.classList.contains('maximized') && modalOverlay) {
            const img = activeContainer.querySelector('img');
            if (!img.contains(e.target)) {
                if (observer) {
                    observer.disconnect();
                    observer = null;
                }
                modalOverlay.remove();
                modalOverlay = null;
                modalImg = null;
                activeContainer.classList.remove('maximized');
                activeContainer = null;
                document.body.style.overflow = '';
            }
        }
    });
});