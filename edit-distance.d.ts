declare module 'edit-distance' {
    // Generic cost function types for lists of T
    type CostFunction<T> = (node: T) => number;
    type UpdateFunction<T> = (nodeA: T, nodeB: T) => number;

    // Tree Edit Distance cost function types
    type TreeCostFunction = (node: any) => number;
    type TreeUpdateFunction = (nodeA: any, nodeB: any) => number;
    type ChildrenFunction = (node: any) => any[];

    // Levenshtein result type (generic T for lists)
    interface LevenshteinResult<T> {
        distance: number;
        pairs(): Array<[T, T]>;
        alignment(): Array<[T, T]>;
    }

    // Tree Edit Distance result type
    interface TreeEditDistanceResult {
        distance: number;
        pairs(): Array<[any, any]>;
        alignment(): Array<[any, any]>;
    }

    // Levenshtein function: works for both string and arrays of T
    function levenshtein<T>(
        sequenceA: string | T[],
        sequenceB: string | T[],
        insert: CostFunction<T | string>,
        remove: CostFunction<T | string>,
        update: UpdateFunction<T | string>,
    ): LevenshteinResult<T | string>;

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
