import * as assert from 'assert';
import Distance from '../../Distance';

suite('Distance Test Suite', () => {
    test('test test name distance', () => {
        const testName1 = 'test_default_value';
        const testName2 = 'test_default_constructor';
        const distance = Distance.testnameDistance(testName1, testName2);
        assert.strictEqual(distance, 10);
    });
    test('Test Filepath Distance', () => {
        const testFilepath = '/home/user/tests/code/subdir/test_main.py';
        const sourceFilepath = '/home/user/src/code/main.py';
        const distance = Distance.filepathDistance(sourceFilepath, testFilepath);
        assert.strictEqual(distance, 2);
        const reverseDistance = Distance.filepathDistance(testFilepath, sourceFilepath);
        assert.strictEqual(reverseDistance, 3);
    });
});
