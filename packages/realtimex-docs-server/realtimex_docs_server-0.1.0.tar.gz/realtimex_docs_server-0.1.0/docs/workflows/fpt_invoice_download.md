# Workflow: FPT Portal Invoice Download

## Overview
Download the requested number of most recent paid invoices from the FPT portal using the documented browser coordinates and timing requirements. This workflow assumes the portal is accessed via Firefox on the standard workstation configuration. Always follow the documented steps in order and insert the mandated pauses after each UI interaction.

## Prerequisites
- Valid FPT portal credentials supplied by the user (username and password).
- Stable internet connection.
- Firefox browser installed and accessible at the documented dock position.
- Download directory configured to save invoices without additional prompts.

## Coordinate Reference (1920×1080 desktop)
| Element | Coordinates (x, y) | Notes |
| --- | --- | --- |
| `firefox_icon` | (300, 975) | Dock icon to launch Firefox |
| `browser_address_bar` | (400, 90) | Address bar for URL entry |
| `username_field` | (260, 495) | Username input field |
| `username_submit_button` | (300, 580) | Button that advances from username entry to password entry |
| `password_field` | (310, 520) | Password input field |
| `login_button_final` | (320, 640) | Final login button |
| `contracts_menu` | (80, 375) | “Hợp Đồng” menu item |
| `view_invoices_link` | (1085, 475) | “xem hóa đơn” link |
| `paid_invoices_tab` | (430, 335) | “Đã thanh toán” tab |
| `first_invoice_download_button` | (1200, 470) | Download button for newest invoice |

**Invoice Row Offset**: Each additional invoice download button is 80 px lower on the y-axis. Apply `y + (n * 80)` for the n-th invoice (0-indexed).

## Step-by-Step Procedure
1. **Launch Firefox**
   - Move to `firefox_icon`, single click, wait 1 second for the browser window.
2. **Navigate to Login Page**
   - Click `browser_address_bar`, type `https://onmember.fpt.vn/login`, press `enter`, wait 2 seconds for page load.
3. **Enter Username**
   - Click `username_field`, type the provided username, click `username_submit_button`, wait 1 second for password field to appear.
4. **Enter Password**
   - Click `password_field`, type the provided password, click `login_button_final`, wait 3 seconds for dashboard.
5. **Open Contracts Page**
   - Click `contracts_menu`, wait 1 second for navigation.
6. **Open Invoices**
   - Click `view_invoices_link`, wait 2 seconds for invoice list.
7. **Filter Paid Invoices**
   - Click `paid_invoices_tab`, wait 2 seconds for tab content to refresh.
8. **Download Invoices**
   - For each invoice index `n` from 0 up to the requested count minus one:
     - Compute `y = 470 + (n * 80)`.
     - Move to `(1200, y)`, click to start the download, and wait 1 second before proceeding to the next invoice.
9. **Confirm Completion**
   - Verify both downloads initiated (e.g., download shelf or folder confirmation) as per local environment conventions.

## Recovery Guidance
- If a page does not load within the expected wait time, allow an additional 3 seconds, then retry the previous step once.
- If coordinates no longer match on-screen elements, **STOP AND ESCALATE** for updated documentation.
- For authentication failures, report the error without reattempting unless explicitly instructed.

## Completion Criteria
- Two most recent paid invoices have download processes started successfully.
- Final report includes the workflow name, key actions, and confirmation that both downloads began (no sensitive data).
