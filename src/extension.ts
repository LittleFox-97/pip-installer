import * as vscode from 'vscode';
import { MissingImportsCodeActionProvider } from './MissingImportsCodeActionProvider';
import { getInstalledPackages } from './utils/listPackage';

export function activate(context: vscode.ExtensionContext) {
    const installPackageCommand = vscode.commands.registerCommand('extension.installPackage', (type: string, args: string) => {
        terminalCommand(`${type} install ${args}`);
    });

    const createPipenvCommand = vscode.commands.registerCommand('extension.createPipenv', (version: string) => {
        // проверяем установлен ли pipenv глобально
        getInstalledPackages().then((packages: string[]) => {
            if (!packages.includes('pipenv')) {
                vscode.window.showErrorMessage('pipenv is not installed. Install pipenv?', 'Yes', 'No').then((selection) => {
                    if (selection === 'Yes') {
                        terminalCommand('pip install pipenv');
                    }
                    if (selection === 'No') {
                        vscode.window.showInformationMessage('pipenv is not installed. Create virtual environment.')
                        vscode.commands.executeCommand('python.createEnvironment');
                    }
                });
                return;
            }
            terminalCommand(`pipenv --python ${version}`)
        }).catch((error) => {
            console.error('Error getting installed packages:', error);
        })
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

// проверяем установлен ли pipenv глобально

export function deactivate() { }
