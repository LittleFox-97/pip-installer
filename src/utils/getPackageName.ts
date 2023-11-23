/**
 * Извлекает имя пакета из строки
 * @param {string} str - Входная строка
 * @returns {string} - Имя пакета
 */
export default function extractPackageName(str: string): string {
    const packageNameMatch = str.match(/(?<=")[^"]+(?=")/);
    if (!packageNameMatch) {
        throw new Error('Text within double quotes not found');
    }
    const packageName = packageNameMatch[0];

    return packageName.includes('.') ? packageName.split('.')[0] : packageName;
}
