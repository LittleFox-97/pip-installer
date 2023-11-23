import { PythonExtension } from '@vscode/python-extension';
import * as vscode from 'vscode';
export class VirtualEnvNotFoundError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "VirtualEnvNotFoundError";
    }
}

class VirtualEnvInstaller {
    static install(version: string) {
        // выводим сообщение об ошибке
        void vscode.window.showErrorMessage("Virtual environment not installed. Choose type:", "Pipenv", "Venv").then((selection) => {
            if (selection === 'Pipenv') {
                void vscode.commands.executeCommand('extension.createPipenv', version);
            }
            if (selection === 'Venv') {
                // запускаем команду создания venv
                void vscode.commands.executeCommand('python.createEnvironment');
            }
        });
    }
}

export default VirtualEnvInstaller;

export async function getEnvType(): Promise<string | undefined> {
    const pythonApi = await PythonExtension.api();
    const environmentPath = pythonApi.environments.getActiveEnvironmentPath();
    const env = await pythonApi.environments.resolveEnvironment(environmentPath);
    
    if (env) {
        const type = env.tools[0];
        
        if (!type) {
            const version = `${env.version?.major}.${env.version?.minor}.${env.version?.micro}`;
            VirtualEnvInstaller.install(version);
        }
        
        return type === 'Pipenv' ? 'pipenv' : 'pip';
    }
    
    await vscode.commands.executeCommand('python.setInterpreter');
}


