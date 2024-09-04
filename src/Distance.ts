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
}
