const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');

let mcpServerProcess = null;
let outputChannel = null;

/**
 * Extension 啟動時調用
 */
function activate(context) {
    console.log('Fubon API MCP Server extension is now active');

    // 創建輸出通道
    outputChannel = vscode.window.createOutputChannel('Fubon MCP Server');
    context.subscriptions.push(outputChannel);

    // 註冊命令
    context.subscriptions.push(
        vscode.commands.registerCommand('fubon-mcp.start', startMCPServer)
    );
    context.subscriptions.push(
        vscode.commands.registerCommand('fubon-mcp.stop', stopMCPServer)
    );
    context.subscriptions.push(
        vscode.commands.registerCommand('fubon-mcp.restart', restartMCPServer)
    );
    context.subscriptions.push(
        vscode.commands.registerCommand('fubon-mcp.showLogs', showLogs)
    );

    // 自動啟動 (如果配置啟用)
    const config = vscode.workspace.getConfiguration('fubon-mcp');
    if (config.get('autoStart')) {
        startMCPServer();
    }
}

/**
 * 啟動 MCP Server
 */
async function startMCPServer() {
    if (mcpServerProcess) {
        vscode.window.showWarningMessage('Fubon MCP Server 已經在運行中');
        return;
    }

    try {
        const config = vscode.workspace.getConfiguration('fubon-mcp');
        const username = config.get('username');
        const pfxPath = config.get('pfxPath');
        const dataDir = config.get('dataDir');

        if (!username || !pfxPath) {
            vscode.window.showErrorMessage(
                '請先在設定中配置富邦證券帳號和憑證路徑 (fubon-mcp.username, fubon-mcp.pfxPath)'
            );
            return;
        }

        // 提示輸入密碼
        const password = await vscode.window.showInputBox({
            prompt: '請輸入富邦證券密碼',
            password: true,
            placeHolder: '密碼不會被儲存'
        });

        if (!password) {
            vscode.window.showWarningMessage('未輸入密碼，取消啟動');
            return;
        }

        const pfxPassword = await vscode.window.showInputBox({
            prompt: '請輸入 PFX 憑證密碼 (如果有)',
            password: true,
            placeHolder: '留空表示無密碼'
        });

        outputChannel.appendLine('正在啟動 Fubon MCP Server...');
        outputChannel.show(true);

        // 設定環境變數
        const env = {
            ...process.env,
            FUBON_USERNAME: username,
            FUBON_PASSWORD: password,
            FUBON_PFX_PATH: pfxPath,
            FUBON_DATA_DIR: dataDir || './data'
        };

        if (pfxPassword) {
            env.FUBON_PFX_PASSWORD = pfxPassword;
        }

        // 啟動 Python MCP Server
        mcpServerProcess = spawn('python', ['-m', 'fubon_mcp.server'], {
            env: env,
            cwd: vscode.workspace.rootPath || process.cwd()
        });

        mcpServerProcess.stdout.on('data', (data) => {
            outputChannel.appendLine(`[OUT] ${data.toString()}`);
        });

        mcpServerProcess.stderr.on('data', (data) => {
            outputChannel.appendLine(`[ERR] ${data.toString()}`);
        });

        mcpServerProcess.on('close', (code) => {
            outputChannel.appendLine(`Fubon MCP Server 已停止 (exit code: ${code})`);
            mcpServerProcess = null;
            
            if (code !== 0) {
                vscode.window.showErrorMessage(`Fubon MCP Server 異常退出 (code: ${code})`);
            }
        });

        mcpServerProcess.on('error', (error) => {
            outputChannel.appendLine(`錯誤: ${error.message}`);
            vscode.window.showErrorMessage(`啟動 MCP Server 失敗: ${error.message}`);
            mcpServerProcess = null;
        });

        vscode.window.showInformationMessage('Fubon MCP Server 已啟動');

    } catch (error) {
        outputChannel.appendLine(`啟動失敗: ${error.message}`);
        vscode.window.showErrorMessage(`啟動 MCP Server 失敗: ${error.message}`);
    }
}

/**
 * 停止 MCP Server
 */
function stopMCPServer() {
    if (!mcpServerProcess) {
        vscode.window.showWarningMessage('Fubon MCP Server 未在運行');
        return;
    }

    outputChannel.appendLine('正在停止 Fubon MCP Server...');
    mcpServerProcess.kill();
    mcpServerProcess = null;
    vscode.window.showInformationMessage('Fubon MCP Server 已停止');
}

/**
 * 重啟 MCP Server
 */
async function restartMCPServer() {
    stopMCPServer();
    // 等待一下確保進程已終止
    await new Promise(resolve => setTimeout(resolve, 1000));
    await startMCPServer();
}

/**
 * 顯示日誌
 */
function showLogs() {
    outputChannel.show(true);
}

/**
 * Extension 停用時調用
 */
function deactivate() {
    if (mcpServerProcess) {
        mcpServerProcess.kill();
    }
}

module.exports = {
    activate,
    deactivate
};
