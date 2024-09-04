declare module 'edit-distance' {
    // Levenshtein cost function types
    type CostFunction = (node: string) => number;
    type UpdateFunction = (stringA: string, stringB: string) => number;

    // Tree Edit Distance cost function types
    type TreeCostFunction = (node: any) => number;
    type TreeUpdateFunction = (nodeA: any, nodeB: any) => number;
    type ChildrenFunction = (node: any) => any[];

    // Levenshtein result type
    interface LevenshteinResult {
        distance: number;
        pairs(): Array<[string, string]>;
        alignment(): Array<[string, string]>;
    }

    // Tree Edit Distance result type
    interface TreeEditDistanceResult {
        distance: number;
        pairs(): Array<[any, any]>;
        alignment(): Array<[any, any]>;
    }

    // Levenshtein function
    function levenshtein(
        stringA: string,
        stringB: string,
        insert: CostFunction,
        remove: CostFunction,
        update: UpdateFunction,
    ): LevenshteinResult;

    // Tree Edit Distance function
    function ted(
        rootA: any,
        rootB: any,
        children: ChildrenFunction,
        insert: TreeCostFunction,
        remove: TreeCostFunction,
        update: TreeUpdateFunction,
    ): TreeEditDistanceResult;
}
