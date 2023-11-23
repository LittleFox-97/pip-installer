import * as childProcess from 'child_process';

export async function getInstalledPackages(): Promise<string[]> {
    return new Promise<string[]>((resolve, reject) => {
        const command = `pip list --format=freeze`;

        childProcess.exec(command, (error, stdout) => {
            if (error) {
                reject(error);
            } else {
                const packages = stdout.trim().split('\n').map(line => line.split('==')[0]);
                resolve(packages);
            }
        });
    });
}

