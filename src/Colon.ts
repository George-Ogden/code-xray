export function escapeColons(text: string): string {
    return text.replace(/:/g, '\\:');
}

export function unescapeColons(text: string): string {
    return text.replace(/\\:/g, ':');
}
