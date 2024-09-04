import * as ed from 'edit-distance';

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
        let sourcePathComponents = sourceFilepath.split('/');
        let testPathComponents = testFilepath.split('/');
        const sourceBasename = sourcePathComponents[sourcePathComponents.length - 1];
        const testBasename = testPathComponents[testPathComponents.length - 1];
        sourcePathComponents = sourcePathComponents.slice(0, sourcePathComponents.length - 1);
        testPathComponents = testPathComponents.slice(0, testPathComponents.length - 1);
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
}
