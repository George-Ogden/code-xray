import * as assert from 'assert';
import { escapeColons, unescapeColons } from '../../Colon';

suite('Colon Test Suite', () => {
    const testCases: { unescaped: string; escaped: string }[] = [
        { unescaped: 'filename.py', escaped: 'filename.py' },
        { unescaped: 'file:with:colons.py', escaped: 'file\\:with\\:colons.py' },
        { unescaped: 'filewithdouble::colons.py', escaped: 'filewithdouble\\:\\:colons.py' },
    ];

    testCases.forEach(({ unescaped, escaped }) => {
        test(`should escape and unescape "${unescaped}" correctly`, () => {
            assert.strictEqual(escapeColons(unescaped), escaped);
            assert.strictEqual(unescapeColons(escaped), unescaped);
        });
    });
});
