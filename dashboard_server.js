const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
require('dotenv').config();

const app = express();
const PORT = 5000;

app.use(express.json());

// OAuth Callback Interceptor
app.get('/admin/success.html', async (req, res) => {
    const { code } = req.query;
    
    if (code) {
        console.log('[OAuth] Received code, exchanging for token...');
        
        const clientId = process.env.PINTEREST_APP_ID || "1562363";
        const clientSecret = process.env.PINTEREST_APP_SECRET;
        const redirectUri = "http://localhost:5000/admin/success.html";
        
        try {
            const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
            const response = await fetch('https://api.pinterest.com/v5/oauth/token', {
                method: 'POST',
                headers: {
                    'Authorization': `Basic ${auth}`,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirectUri
                })
            });
            
            const data = await response.json();
            
            if (data.access_token) {
                console.log('[OAuth] Token exchange successful!');
                fs.writeFileSync(path.join(__dirname, 'pinterest_token.json'), JSON.stringify(data, null, 2));
            } else {
                console.error('[OAuth] Token exchange failed:', data);
            }
        } catch (err) {
            console.error('[OAuth] Error during exchange:', err.message);
        }
    }
    
    res.sendFile(path.join(__dirname, 'bridge_page', 'admin', 'success.html'));
});

app.use('/admin', express.static(path.join(__dirname, 'bridge_page', 'admin')));

// Serve the generated images so the dashboard can show them
app.use('/temp', express.static(path.join(__dirname)));

// Root redirect
app.get('/', (req, res) => {
    res.redirect('/admin');
});

// Real API for Pin Generation
app.post('/api/generate', (req, res) => {
    const { trend } = req.body;
    console.log(`[Server] Triggering generation for: ${trend}`);

    // Try 'py' first on Windows, then 'python'
    function runPython(cmd) {
        const scriptPath = path.join(__dirname, 'pinterest_engine', 'pin_generator.py');
        console.log(`[Server] Executing: ${cmd} ${scriptPath}`);
        const pythonProcess = spawn(cmd, [
            scriptPath,
            '--trend', trend,
            '--count', '1'
        ]);

        let hasResponded = false;
        let stderrData = '';

        pythonProcess.on('error', (err) => {
            console.error(`[Server Error] Failed to start (${cmd}):`, err.message);
            if (!hasResponded) {
                if (cmd === 'py') {
                    runPython('python'); // Try 'python' as fallback
                } else {
                    hasResponded = true;
                    res.status(500).json({ success: false, error: 'Python not found.' });
                }
            }
        });

        let pinUrl = 'https://www.pinterest.com/FoodTrendsBlog/sandbox/';

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`[Python] ${output}`);
            const match = output.match(/PIN_PUBLISHED_URL: (https:\/\/www\.pinterest\.com\/pin\/\d+\/|https:\/\/www\.pinterest\.com\/FoodTrendsBlog\/sandbox\/)/);
            if (match) {
                pinUrl = match[1];
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            stderrData += data.toString();
            console.error(`[Python Error] ${data}`);
        });

        pythonProcess.on('close', (code) => {
            if (hasResponded) return;

            // Handle the "Microsoft Store" fake python error
            if (code !== 0 && (stderrData.includes('Python was not found') || stderrData.includes('install from the Microsoft Store'))) {
                console.log(`[Server] '${cmd}' is a placeholder. Trying fallback...`);
                if (cmd === 'py') {
                    runPython('python');
                } else if (cmd === 'python') {
                    runPython('py');
                }
                return;
            }

            hasResponded = true;
            if (code === 0) {
                res.json({ 
                    success: true, 
                    pinUrl: pinUrl,
                    title: trend 
                });
            } else {
                res.status(500).json({ success: false, error: `Generation failed with code ${code}` });
            }
        });
    }

    runPython('py'); // Start with 'py' on Windows
});

// Mock API for trend data
app.get('/api/trends', (req, res) => {
    res.json([
        { keyword: "Viral Cloud Cake", category: "Baking", growth: "+240%", status: "Covered" },
        { keyword: "Matcha Tiramisu", category: "Fusion", growth: "+180%", status: "Processing" },
        { keyword: "Pistachio Kunafa Spread", category: "Sweets", growth: "+410%", status: "New" }
    ]);
});

// Start server
app.listen(PORT, () => {
    console.log(`
=========================================
  FOOD TRENDS AUTOMATION - ADMIN SERVER
=========================================
Server running at: http://localhost:${PORT}/admin

Use this server to record your Pinterest 
Standard Access demo video.
=========================================
    `);
});
