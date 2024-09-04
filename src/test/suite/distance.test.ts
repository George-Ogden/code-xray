import * as assert from 'assert';
import Distance from '../../Distance';

suite('Distance Test Suite', () => {
    test('test test name distance', () => {
        const testName1 = 'test_default_value';
        const testName2 = 'test_default_constructor';
        const distance = Distance.testnameDistance(testName1, testName2);
        assert.strictEqual(distance, 10);
    });
});
