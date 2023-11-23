import * as vscode from 'vscode';

import { getEnvType } from './utils/evnType';
import extractPackageName from './utils/getPackageName';

export class MissingImportsCodeActionProvider implements vscode.CodeActionProvider {
    provideCodeActions(document: vscode.TextDocument, range: vscode.Range, context: vscode.CodeActionContext): vscode.ProviderResult<vscode.CodeAction[]> {
        const codeActions: vscode.CodeAction[] = [];
        const diagnostic = context.diagnostics.find(diagnostic => {
            const { source, code } = diagnostic;
            return (typeof code === 'object' ? code?.value === 'reportMissingImports' || code?.value === 'reportMissingModuleSource' : false) && source === 'Pylance';
        });

        if (!diagnostic) {
            return Promise.resolve(codeActions);
        }

        const packageName = extractPackageName(diagnostic.message);
        const typePromise = getEnvType();

        return typePromise.then(type => {
            codeActions.push(...createCodeActions(type, packageName));
            return codeActions;
        }).catch(error => {
            console.error('ERROR:', error);
            return Promise.reject(error);
        });
    }
}

function createCodeActions(type: string|undefined, packageName: string): vscode.CodeAction[] {
    const codeActions: vscode.CodeAction[] = [];

    if (type === 'pipenv') {
        const devPackageAction = new vscode.CodeAction(
            `Install dev package ${packageName}`,
            vscode.CodeActionKind.QuickFix
        );
        devPackageAction.command = {
            command: 'extension.installPackage',
            title: `Install dev package ${packageName}`,
            arguments: [type, '--dev', packageName]
        };

        codeActions.push(devPackageAction);
    }

    if (type === 'pip') {
        const installPackageAction = new vscode.CodeAction(
            `Install package ${packageName}`,
            vscode.CodeActionKind.QuickFix
        );
        installPackageAction.command = {
            command: 'extension.installPackage',
            title: `Install package ${packageName}`,
            arguments: [type, packageName]
        };

        codeActions.push(installPackageAction);
    }

    return codeActions;
}