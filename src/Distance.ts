import * as ed from 'edit-distance';
import path = require('path');

export default class Distance {
    private static constant(x: any): number {
        return 1;
    }
    private static stringUpdateCost(a: string, b: string): number {
        return a === b ? 0 : 1;
    }
    public static testnameDistance(stringA: string, stringB: string): number {
        return ed.levenshtein(stringA, stringB, this.constant, this.constant, this.stringUpdateCost).distance;
    }
    private static filenameUpdateCost(sourceBasename: string, testBasename: string): number {
        return testBasename.split('.')[0].includes(sourceBasename.split('.')[0]) ? 0 : 1;
    }
    public static filepathDistance(sourceFilepath: string, testFilepath: string): number {
        const sourceBasename = path.basename(sourceFilepath);
        const sourceDirname = path.dirname(sourceFilepath);
        const testBasename = path.basename(testFilepath);
        let testDirname = path.dirname(testFilepath);
        if (!path.isAbsolute(testDirname)) {
            testDirname = path.normalize(path.join(sourceDirname, testDirname));
        }
        const sourcePathComponents = sourceDirname.split(path.sep);
        const testPathComponents = testDirname.split(path.sep);
        return (
            ed.levenshtein(
                sourcePathComponents,
                testPathComponents,
                this.constant,
                this.constant,
                this.stringUpdateCost,
            ).distance + this.filenameUpdateCost(sourceBasename, testBasename)
        );
    }
    public static functionNameDistance(functionName: string, testName: string): number {
        testName = testName.toLowerCase();
        return functionName
            .split('.')
            .map((functionPart): number => (testName.includes(functionPart.toLowerCase()) ? 0 : 1))
            .reduce((a, c) => a + c);
    }
}
