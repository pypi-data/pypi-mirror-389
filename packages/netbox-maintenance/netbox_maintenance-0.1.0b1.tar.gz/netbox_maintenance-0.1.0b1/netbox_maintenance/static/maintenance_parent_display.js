/**
 * Enhancement for DynamicModelMultipleChoiceField to show parent information
 * and highlight pre-loaded objects
 */
document.addEventListener('DOMContentLoaded', function () {
    // console.log('[Parent Display] Script loaded');

    // Find all elements with data-preloaded-ids or data-parent-display attribute
    const selectsWithPreloaded = document.querySelectorAll('[data-preloaded-ids]');
    const selectsWithParent = document.querySelectorAll('[data-parent-display]');

    // Combine both NodeLists into a Set to avoid duplicates
    const allSelects = new Set([...selectsWithPreloaded, ...selectsWithParent]);
    // console.log('[Parent Display] Found', allSelects.size, 'elements to enhance');

    allSelects.forEach(function (select) {
        // console.log('[Parent Display] Processing select:', select.id || select.name);

        try {
            // Parse the preloaded IDs (all pre-populated objects)
            const preloadedIdsAttr = select.getAttribute('data-preloaded-ids');
            const preloadedIds = preloadedIdsAttr ? JSON.parse(preloadedIdsAttr) : [];

            // Parse the parent display mapping (only objects with parents)
            const parentDisplayAttr = select.getAttribute('data-parent-display');
            const parentDisplayData = parentDisplayAttr ? JSON.parse(parentDisplayAttr) : {};

            // console.log('[Parent Display] Preloaded IDs:', preloadedIds);
            // console.log('[Parent Display] Parent display data:', parentDisplayData);

            // Function to enhance the display
            function enhanceDisplay() {
                // Get the TomSelect instance
                const tomselect = select.tomselect;

                if (!tomselect) {
                    // console.log('[Parent Display] TomSelect not yet initialized, will retry...');
                    return false;
                }

                // console.log('[Parent Display] TomSelect instance found');

                // First, bold all preloaded items
                preloadedIds.forEach(function (itemId) {
                    const itemElement = tomselect.control.querySelector('[data-value="' + itemId + '"]');
                    if (itemElement) {
                        itemElement.classList.add('fw-bold');
                        // console.log('[Parent Display] Bolded preloaded item', itemId);
                    }
                });

                // Then, update display for items with parent info
                Object.keys(parentDisplayData).forEach(function (itemId) {
                    const data = parentDisplayData[itemId];
                    // console.log('[Parent Display] Processing item', itemId, data);

                    // Update in the options data
                    if (tomselect.options[itemId]) {
                        const enhancedDisplay = data.display + ' (' + data.parent + ')';
                        tomselect.options[itemId].display = enhancedDisplay;
                        // console.log('[Parent Display] Updated option', itemId, 'to', enhancedDisplay);
                    }

                    // Update the rendered item if it's already selected
                    const itemElement = tomselect.control.querySelector('[data-value="' + itemId + '"]');
                    if (itemElement) {
                        // Find the existing remove button to preserve its event handlers
                        const removeButton = itemElement.querySelector('.remove');

                        if (removeButton) {
                            // Remove all child nodes except the remove button
                            Array.from(itemElement.childNodes).forEach(function (node) {
                                if (node !== removeButton) {
                                    itemElement.removeChild(node);
                                }
                            });

                            // Create the enhanced display text
                            const textNode = document.createTextNode(data.display + ' ');
                            const parentSpan = document.createElement('span');
                            parentSpan.className = 'text-secondary';
                            parentSpan.textContent = '(' + data.parent + ')';

                            // Insert before the remove button
                            itemElement.insertBefore(textNode, removeButton);
                            itemElement.insertBefore(parentSpan, removeButton);

                            // Note: fw-bold already added above for all preloaded items

                            // console.log('[Parent Display] Updated rendered item with parent info', itemId);
                        }
                    }
                });

                return true;
            }

            // Try multiple times with increasing delays
            let attempts = 0;
            const maxAttempts = 5;

            function tryEnhance() {
                attempts++;
                // console.log('[Parent Display] Attempt', attempts, 'of', maxAttempts);

                if (enhanceDisplay()) {
                    // console.log('[Parent Display] Successfully enhanced display');
                } else if (attempts < maxAttempts) {
                    setTimeout(tryEnhance, attempts * 200);
                } else {
                    // console.warn('[Parent Display] Failed to enhance display after', maxAttempts, 'attempts');
                }
            }

            // Start trying
            setTimeout(tryEnhance, 100);

        } catch (e) {
            console.error('[Parent Display] Error enhancing parent display:', e);
        }
    });
});
