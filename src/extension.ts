import * as vscode from 'vscode';
import { MissingImportsCodeActionProvider } from './MissingImportsCodeActionProvider';

export function activate(context: vscode.ExtensionContext) {
    const installPackageCommand = vscode.commands.registerCommand('extension.installPackage', (type: string, args: string) => {
        terminalCommand(`${type} install ${args}`);
    });

    const createPipenvCommand = vscode.commands.registerCommand('extension.createPipenv', (version: string) => {
        terminalCommand(`pipenv --python ${version}`);
    });

    const provider = new MissingImportsCodeActionProvider();

    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file', language: 'python' },
            provider
        ),
        installPackageCommand,
        createPipenvCommand
    );
}

export function terminalCommand(textCommand: string): void {
    const terminal = vscode.window.activeTerminal || vscode.window.createTerminal();
    if (terminal) {
        terminal.show();
        terminal.sendText(textCommand);
    }
}

export function deactivate() { }
