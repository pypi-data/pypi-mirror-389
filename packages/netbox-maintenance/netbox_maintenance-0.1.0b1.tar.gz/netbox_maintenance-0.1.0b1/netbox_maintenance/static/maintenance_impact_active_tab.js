/**
 * Activate the correct tab when a preselected object is present
 * Uses data-active-tab attribute to identify which tab should be active
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('[MaintenanceImpact] Tab activation script loaded');

    // Find the select field marked with data-active-tab
    const activeSelect = document.querySelector('select[data-active-tab="true"]');

    if (!activeSelect) {
        console.log('[MaintenanceImpact] No active tab marker found');
        return;
    }

    console.log('[MaintenanceImpact] Found active tab marker on select:', activeSelect.id || activeSelect.name);

    // Function to activate the tab
    function activateTab() {
        // Find the tab panel containing this select
        const tabPanel = activeSelect.closest('[role="tabpanel"]');

        if (!tabPanel) {
            console.log('[MaintenanceImpact] Select not in a tab panel, will retry...');
            return false;
        }

        console.log('[MaintenanceImpact] Found tab panel:', tabPanel.id);

        // Find the tab button that controls this panel
        const panelId = tabPanel.id;
        const tabButton = document.querySelector('[data-bs-target="#' + panelId + '"]');

        if (!tabButton) {
            console.log('[MaintenanceImpact] Tab button not found for panel', panelId);
            return false;
        }

        console.log('[MaintenanceImpact] Found tab button:', tabButton.id);

        // Find all tab buttons and panels in the same group
        const tabList = tabButton.closest('[role="tablist"]');
        if (!tabList) {
            console.log('[MaintenanceImpact] Tab list not found');
            return false;
        }

        const allTabButtons = tabList.querySelectorAll('[role="tab"]');

        // Find the tab-content container
        const row = tabList.closest('.row');
        const tabContent = row ? row.nextElementSibling : null;

        if (!tabContent || !tabContent.classList.contains('tab-content')) {
            console.log('[MaintenanceImpact] Tab content container not found');
            return false;
        }

        const allTabPanels = tabContent.querySelectorAll('[role="tabpanel"]');

        console.log('[MaintenanceImpact] Found', allTabButtons.length, 'tab buttons and', allTabPanels.length, 'tab panels');

        // Deactivate all tabs
        allTabButtons.forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
            btn.setAttribute('tabindex', '-1');
        });
        allTabPanels.forEach(panel => {
            panel.classList.remove('show', 'active');
        });

        // Activate the target tab
        tabButton.classList.add('active');
        tabButton.setAttribute('aria-selected', 'true');
        tabButton.removeAttribute('tabindex');

        tabPanel.classList.add('show', 'active');

        //console.log('[MaintenanceImpact] Successfully activated tab:', tabButton.textContent.trim());
        return true;
    }

    // Try multiple times with increasing delays (similar to maintenance_parent_display.js)
    let attempts = 0;
    const maxAttempts = 5;

    function tryActivate() {
        attempts++;
        //console.log('[MaintenanceImpact] Attempt', attempts, 'of', maxAttempts);

        if (activateTab()) {
            console.log('[MaintenanceImpact] Successfully activated tab');
        } else if (attempts < maxAttempts) {
            setTimeout(tryActivate, attempts * 200);
        } else {
            console.warn('[MaintenanceImpact] Failed to activate tab after', maxAttempts, 'attempts');
        }
    }

    // Start trying after a small delay
    setTimeout(tryActivate, 100);
});
