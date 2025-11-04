def doc():
    print(r"""
funcName->.......
activityselection, 
binomialcoeff, 
chainmatmul, 
dijkistra, 
fibonacci, 
floyd, 
heapsort, 
huffman, 
jobshedulingdeadline, 
knacksnap, 
knacksnapdp, 
knacksnapfractional, 
longestcommonsubseq, 
longestpalindrom, 
mergesort, 
nqueen, 
pairsort, 
primkruskal, 
quicksort, 
sttarsanmulti,
binarytreemaxpathsum,
maximumscorewordsformedbyletters,
meetingroom3,
counthighestscorenodes,
maxtaxiearnings,
reversepairs,
superpow,
diffwaystocomputeparanthesis,
reversekgroup,
findkthnumberinmultiplicationtable
""")

    
def knacksnap():
    print(r"""
import java.util.Scanner;

public class KnapsackRecursive {

    // Recursive function for 0/1 Knapsack
    public static int knapsack(int[] weights, int[] values, int capacity, int n) {
        // Base case
        if (n == 0 || capacity == 0)
            return 0;

        // If the current item's weight is more than the capacity, skip it
        if (weights[n - 1] > capacity)
            return knapsack(weights, values, capacity, n - 1);

        // Otherwise, choose the maximum between including or excluding the item
        else {
            int include = values[n - 1] + knapsack(weights, values, capacity - weights[n - 1], n - 1);
            int exclude = knapsack(weights, values, capacity, n - 1);
            return Math.max(include, exclude);
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("         0/1 KNAPSACK PROBLEM");
        System.out.println("       (Recursive Implementation)");
        System.out.println("=======================================");

        System.out.print("Please enter the number of items: ");
        int n = sc.nextInt();

        int[] weights = new int[n];
        int[] values = new int[n];

        System.out.println("\n=======================================");
        System.out.println("         ENTER ITEM DETAILS");
        System.out.println("=======================================");

        for (int i = 0; i < n; i++) {
            System.out.println("\nItem " + (i + 1) + ":");
            System.out.print("  Enter weight: ");
            weights[i] = sc.nextInt();
            System.out.print("  Enter value:  ");
            values[i] = sc.nextInt();
        }

        System.out.println("\n=======================================");
        System.out.print("Please enter the knapsack capacity: ");
        int capacity = sc.nextInt();

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING RESULT...");
        System.out.println("=======================================");

        int maxValue = knapsack(weights, values, capacity, n);

        System.out.println("\nThe maximum value that can be obtained = " + maxValue);
        System.out.println("=======================================");

        sc.close();
    }
}


""")
def knacksnapfractional():
    print(r"""
import java.util.*;

public class FractionalKnapsack {
    static class Item {
        int weight;
        int value;
        double ratio;
        Item(int weight, int value) {
            this.weight = weight;
            this.value = value;
            this.ratio = (double) value / weight;
        }
    }

    public static double fractionalKnapsack(int capacity, Item[] items) {
        Arrays.sort(items, (a, b) -> Double.compare(b.ratio, a.ratio));
        double totalValue = 0.0;
        for (Item item : items) {
            if (capacity >= item.weight) {
                capacity -= item.weight;
                totalValue += item.value;
            } else {
                totalValue += item.value * ((double) capacity / item.weight);
                break;
            }
        }
        return totalValue;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("        FRACTIONAL KNAPSACK PROBLEM");
        System.out.println("=======================================");

        System.out.print("Please enter the number of items: ");
        int n = sc.nextInt();

        Item[] items = new Item[n];

        System.out.println("\n=======================================");
        System.out.println("         ENTER ITEM DETAILS");
        System.out.println("=======================================");

        for (int i = 0; i < n; i++) {
            System.out.println("\nItem " + (i + 1) + ":");
            System.out.print("  → Enter weight: ");
            int w = sc.nextInt();
            System.out.print("  → Enter value:  ");
            int v = sc.nextInt();
            items[i] = new Item(w, v);
        }

        System.out.println("\n=======================================");
        System.out.print("Please enter the knapsack capacity: ");
        int capacity = sc.nextInt();

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING RESULT...");
        System.out.println("=======================================");

        double maxValue = fractionalKnapsack(capacity, items);

        System.out.println("\nThe maximum value that can be obtained = " + maxValue);
        System.out.println("=======================================");

        sc.close();
    }
}

""")
def activityselection():
    print(r"""
import java.util.*;

public class ActivitySelection {
    static class Activity {
        int start;
        int end;
        Activity(int start, int end) {
            this.start = start;
            this.end = end;
        }
    }

    public static int maxActivities(Activity[] activities) {
        Arrays.sort(activities, Comparator.comparingInt(a -> a.end));
        int count = 1;
        int lastEnd = activities[0].end;
        for (int i = 1; i < activities.length; i++) {
            if (activities[i].start >= lastEnd) {
                count++;
                lastEnd = activities[i].end;
            }
        }
        return count;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("        ACTIVITY SELECTION PROBLEM");
        System.out.println("=======================================");

        System.out.print("Please enter the number of activities: ");
        int n = sc.nextInt();

        Activity[] activities = new Activity[n];

        System.out.println("\n=======================================");
        System.out.println("         ENTER ACTIVITY DETAILS");
        System.out.println("=======================================");

        for (int i = 0; i < n; i++) {
            System.out.println("\nActivity " + (i + 1) + ":");
            System.out.print("  → Enter start time: ");
            int s = sc.nextInt();
            System.out.print("  → Enter end time:   ");
            int e = sc.nextInt();
            activities[i] = new Activity(s, e);
        }

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING RESULT...");
        System.out.println("=======================================");

        int maxCount = maxActivities(activities);

        System.out.println("\nThe maximum number of non-overlapping activities = " + maxCount);
        System.out.println("=======================================");

        sc.close();
    }
}

""")
def jobshedulingdeadline():
    print(r"""
import java.util.*;

public class JobScheduling {
    static class Job {
        char id;
        int deadline;
        int profit;
        Job(char id, int deadline, int profit) {
            this.id = id;
            this.deadline = deadline;
            this.profit = profit;
        }
    }

    public static void jobScheduling(Job[] jobs) {
        Arrays.sort(jobs, (a, b) -> b.profit - a.profit);
        int n = jobs.length;
        int maxDeadline = 0;
        for (Job job : jobs) {
            if (job.deadline > maxDeadline)
                maxDeadline = job.deadline;
        }

        char[] result = new char[maxDeadline + 1];
        boolean[] slot = new boolean[maxDeadline + 1];
        int totalProfit = 0;

        for (Job job : jobs) {
            for (int j = job.deadline; j > 0; j--) {
                if (!slot[j]) {
                    slot[j] = true;
                    result[j] = job.id;
                    totalProfit += job.profit;
                    break;
                }
            }
        }

        System.out.println("\n=======================================");
        System.out.println("        JOB SEQUENCE SELECTED");
        System.out.println("=======================================");
        for (int i = 1; i <= maxDeadline; i++) {
            if (slot[i])
                System.out.print(result[i] + " ");
        }
        System.out.println("\nTotal Profit = " + totalProfit);
        System.out.println("=======================================");
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("        JOB SCHEDULING PROBLEM");
        System.out.println("=======================================");

        System.out.print("Please enter the number of jobs: ");
        int n = sc.nextInt();

        Job[] jobs = new Job[n];

        System.out.println("\n=======================================");
        System.out.println("         ENTER JOB DETAILS");
        System.out.println("=======================================");

        for (int i = 0; i < n; i++) {
            System.out.println("\nJob " + (i + 1) + ":");
            System.out.print("  → Enter Job ID (single character): ");
            char id = sc.next().charAt(0);
            System.out.print("  → Enter deadline: ");
            int deadline = sc.nextInt();
            System.out.print("  → Enter profit:   ");
            int profit = sc.nextInt();
            jobs[i] = new Job(id, deadline, profit);
        }

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING RESULT...");
        System.out.println("=======================================");

        jobScheduling(jobs);

        sc.close();
    }
}

""")
def huffman():
    print(r"""
import java.util.*;

public class HuffmanEncoding {
    static class Node {
        char ch;
        int freq;
        Node left, right;
        Node(char ch, int freq) {
            this.ch = ch;
            this.freq = freq;
        }
    }

    static class CompareNode implements Comparator<Node> {
        public int compare(Node a, Node b) {
            return a.freq - b.freq;
        }
    }

    public static void buildCodeMap(Node root, String code, Map<Character, String> huffmanCode) {
        if (root == null)
            return;
        if (root.left == null && root.right == null)
            huffmanCode.put(root.ch, code);
        buildCodeMap(root.left, code + "0", huffmanCode);
        buildCodeMap(root.right, code + "1", huffmanCode);
    }

    public static void huffmanEncode(String text) {
        Map<Character, Integer> freqMap = new HashMap<>();
        for (char ch : text.toCharArray())
            freqMap.put(ch, freqMap.getOrDefault(ch, 0) + 1);

        PriorityQueue<Node> pq = new PriorityQueue<>(new CompareNode());
        for (Map.Entry<Character, Integer> entry : freqMap.entrySet())
            pq.add(new Node(entry.getKey(), entry.getValue()));

        while (pq.size() > 1) {
            Node left = pq.poll();
            Node right = pq.poll();
            Node parent = new Node('-', left.freq + right.freq);
            parent.left = left;
            parent.right = right;
            pq.add(parent);
        }

        Node root = pq.peek();
        Map<Character, String> huffmanCode = new HashMap<>();
        buildCodeMap(root, "", huffmanCode);

        System.out.println("\n=======================================");
        System.out.println("         CHARACTER CODES");
        System.out.println("=======================================");
        for (Map.Entry<Character, String> entry : huffmanCode.entrySet())
            System.out.println(entry.getKey() + " : " + entry.getValue());

        StringBuilder encoded = new StringBuilder();
        for (char ch : text.toCharArray())
            encoded.append(huffmanCode.get(ch));

        System.out.println("\n=======================================");
        System.out.println("         ENCODED STRING");
        System.out.println("=======================================");
        System.out.println(encoded.toString());
        System.out.println("=======================================");
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("            HUFFMAN ENCODING");
        System.out.println("=======================================");

        System.out.print("Please enter the string to encode: ");
        String text = sc.nextLine();

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING FREQUENCIES...");
        System.out.println("=======================================");

        huffmanEncode(text);

        sc.close();
    }
}

""")
def primkruskal():
    print(r"""
import java.util.*;

public class MSTNoDisjoint {

    static class Edge {
        int src, dest, weight;
        Edge(int src, int dest, int weight) {
            this.src = src;
            this.dest = dest;
            this.weight = weight;
        }
    }

    public static void kruskalMST(List<Edge> edges, int vertices) {
        Collections.sort(edges, Comparator.comparingInt(e -> e.weight));
        int[] parent = new int[vertices];
        for (int i = 0; i < vertices; i++)
            parent[i] = i;

        List<Edge> result = new ArrayList<>();
        int totalWeight = 0;

        for (Edge edge : edges) {
            int srcParent = findParent(parent, edge.src);
            int destParent = findParent(parent, edge.dest);

            if (srcParent != destParent) {
                result.add(edge);
                totalWeight += edge.weight;
                parent[destParent] = srcParent;
            }
        }

        System.out.println("\n=======================================");
        System.out.println("          KRUSKAL'S MST RESULT");
        System.out.println("=======================================");
        for (Edge e : result)
            System.out.println("Edge: " + e.src + " - " + e.dest + " | Weight: " + e.weight);
        System.out.println("Total Weight: " + totalWeight);
        System.out.println("=======================================");
    }

    public static int findParent(int[] parent, int v) {
        while (parent[v] != v)
            v = parent[v];
        return v;
    }

    public static void primsMST(int[][] graph, int vertices) {
        boolean[] visited = new boolean[vertices];
        int[] key = new int[vertices];
        int[] parent = new int[vertices];
        Arrays.fill(key, Integer.MAX_VALUE);
        key[0] = 0;
        parent[0] = -1;

        for (int count = 0; count < vertices - 1; count++) {
            int u = -1;
            for (int i = 0; i < vertices; i++) {
                if (!visited[i] && (u == -1 || key[i] < key[u]))
                    u = i;
            }
            visited[u] = true;
            for (int v = 0; v < vertices; v++) {
                if (graph[u][v] != 0 && !visited[v] && graph[u][v] < key[v]) {
                    parent[v] = u;
                    key[v] = graph[u][v];
                }
            }
        }

        System.out.println("\n=======================================");
        System.out.println("           PRIM'S MST RESULT");
        System.out.println("=======================================");
        int totalWeight = 0;
        for (int i = 1; i < vertices; i++) {
            System.out.println("Edge: " + parent[i] + " - " + i + " | Weight: " + graph[i][parent[i]]);
            totalWeight += graph[i][parent[i]];
        }
        System.out.println("Total Weight: " + totalWeight);
        System.out.println("=======================================");
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("=======================================");
        System.out.println("    KRUSKAL'S & PRIM'S MST ALGORITHMS");
        System.out.println("=======================================");

        System.out.print("Please enter the number of vertices: ");
        int vertices = sc.nextInt();

        System.out.print("Please enter the number of edges: ");
        int edgesCount = sc.nextInt();

        List<Edge> edges = new ArrayList<>();
        int[][] graph = new int[vertices][vertices];

        System.out.println("\n=======================================");
        System.out.println("         ENTER EDGE DETAILS");
        System.out.println("=======================================");

        for (int i = 0; i < edgesCount; i++) {
            System.out.println("\nEdge " + (i + 1) + ":");
            System.out.print("  → Enter source vertex (0 to " + (vertices - 1) + "): ");
            int src = sc.nextInt();
            System.out.print("  → Enter destination vertex (0 to " + (vertices - 1) + "): ");
            int dest = sc.nextInt();
            System.out.print("  → Enter weight: ");
            int weight = sc.nextInt();

            edges.add(new Edge(src, dest, weight));
            graph[src][dest] = weight;
            graph[dest][src] = weight;
        }

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING KRUSKAL'S MST...");
        System.out.println("=======================================");
        kruskalMST(edges, vertices);

        System.out.println("\n=======================================");
        System.out.println("         CALCULATING PRIM'S MST...");
        System.out.println("=======================================");
        primsMST(graph, vertices);

        sc.close();
    }
}

""")
def dijkistra():
    print(r"""
import java.util.*;

public class DijkstraAlgorithm {
    static final int INF = Integer.MAX_VALUE;

    static int minDistance(int[] dist, boolean[] visited, int n) {
        int min = INF, minIndex = -1;
        for (int v = 0; v < n; v++) {
            if (!visited[v] && dist[v] <= min) {
                min = dist[v];
                minIndex = v;
            }
        }
        return minIndex;
    }

    static void dijkstra(int[][] graph, int src, int n) {
        int[] dist = new int[n];
        boolean[] visited = new boolean[n];

        Arrays.fill(dist, INF);
        dist[src] = 0;

        for (int count = 0; count < n - 1; count++) {
            int u = minDistance(dist, visited, n);
            visited[u] = true;

            for (int v = 0; v < n; v++) {
                if (!visited[v] && graph[u][v] != 0 && dist[u] != INF && dist[u] + graph[u][v] < dist[v]) {
                    dist[v] = dist[u] + graph[u][v];
                }
            }
        }

        System.out.println("====== Shortest Distances from Source ======");
        for (int i = 0; i < n; i++) {
            System.out.println("Vertex " + i + " -> " + dist[i]);
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Single Source Shortest Path – Dijkstras Algorithm ======");
        System.out.print("Enter number of vertices: ");
        int n = sc.nextInt();

        int[][] graph = new int[n][n];

        System.out.println("====== Graph Building Section ======");
        System.out.print("Enter number of edges: ");
        int e = sc.nextInt();

        for (int i = 0; i < e; i++) {
            System.out.println("Enter details for edge " + (i + 1) + ":");
            System.out.print("From vertex: ");
            int u = sc.nextInt();
            System.out.print("To vertex: ");
            int v = sc.nextInt();
            System.out.print("Enter weight: ");
            int w = sc.nextInt();
            graph[u][v] = w;
            graph[v][u] = w;
            System.out.println("======");
        }

        System.out.println("====== Adjacency Matrix ======");
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                System.out.print(graph[i][j] + " ");
            }
            System.out.println();
        }

        System.out.print("Enter source vertex: ");
        int src = sc.nextInt();

        dijkstra(graph, src, n);
    }
}

""")
def fibonacci():
    print(r"""
import java.util.*;

public class FibonacciDP {
    static int fibonacci(int n, int[] dp) {
        if (n <= 1) return n;
        if (dp[n] != -1) return dp[n];
        dp[n] = fibonacci(n - 1, dp) + fibonacci(n - 2, dp);
        return dp[n];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Fibonacci Series using Dynamic Programming ======");
        System.out.print("Enter the number of terms: ");
        int n = sc.nextInt();

        int[] dp = new int[n + 1];
        Arrays.fill(dp, -1);

        System.out.println("====== Fibonacci Series ======");
        for (int i = 0; i < n; i++) {
            System.out.print(fibonacci(i, dp) + " ");
        }
        System.out.println();
    }
}

""")
def binomialcoeff():
    print(r"""
import java.util.*;

public class BinomialCoefficientDP {
    static int binomialCoeff(int n, int k, int[][] dp) {
        if (k == 0 || k == n) return 1;
        if (dp[n][k] != -1) return dp[n][k];
        dp[n][k] = binomialCoeff(n - 1, k - 1, dp) + binomialCoeff(n - 1, k, dp);
        return dp[n][k];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Binomial Coefficient using Dynamic Programming ======");
        System.out.print("Enter n: ");
        int n = sc.nextInt();
        System.out.print("Enter k: ");
        int k = sc.nextInt();

        int[][] dp = new int[n + 1][k + 1];
        for (int[] row : dp) Arrays.fill(row, -1);

        int result = binomialCoeff(n, k, dp);
        System.out.println("====== Result ======");
        System.out.println("C(" + n + ", " + k + ") = " + result);
    }
}

""")
def knacksnapdp():
    print(r"""
import java.util.*;

public class KnapsackDP {
    static int knapsack(int W, int[] wt, int[] val, int n, int[][] dp) {
        if (n == 0 || W == 0) return 0;
        if (dp[n][W] != -1) return dp[n][W];

        if (wt[n - 1] <= W)
            dp[n][W] = Math.max(val[n - 1] + knapsack(W - wt[n - 1], wt, val, n - 1, dp),
                                knapsack(W, wt, val, n - 1, dp));
        else
            dp[n][W] = knapsack(W, wt, val, n - 1, dp);

        return dp[n][W];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== 0/1 Knapsack Problem using Dynamic Programming ======");
        System.out.print("Enter number of items: ");
        int n = sc.nextInt();

        int[] wt = new int[n];
        int[] val = new int[n];

        System.out.println("====== Enter item weights and values ======");
        for (int i = 0; i < n; i++) {
            System.out.print("Weight of item " + (i + 1) + ": ");
            wt[i] = sc.nextInt();
            System.out.print("Value of item " + (i + 1) + ": ");
            val[i] = sc.nextInt();
            System.out.println("======");
        }

        System.out.print("Enter knapsack capacity: ");
        int W = sc.nextInt();

        int[][] dp = new int[n + 1][W + 1];
        for (int[] row : dp) Arrays.fill(row, -1);

        int maxValue = knapsack(W, wt, val, n, dp);

        System.out.println("====== Result ======");
        System.out.println("Maximum value that can be obtained = " + maxValue);
    }
}

""")
def longestcommonsubseq():
    print(r"""
import java.util.*;

public class LongestCommonSubsequenceDP {
    static int lcs(String X, String Y, int m, int n, int[][] dp) {
        if (m == 0 || n == 0) return 0;
        if (dp[m][n] != -1) return dp[m][n];

        if (X.charAt(m - 1) == Y.charAt(n - 1))
            dp[m][n] = 1 + lcs(X, Y, m - 1, n - 1, dp);
        else
            dp[m][n] = Math.max(lcs(X, Y, m - 1, n, dp), lcs(X, Y, m, n - 1, dp));

        return dp[m][n];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Longest Common Subsequence using Dynamic Programming ======");
        System.out.print("Enter first string: ");
        String X = sc.nextLine();
        System.out.print("Enter second string: ");
        String Y = sc.nextLine();

        int m = X.length();
        int n = Y.length();

        int[][] dp = new int[m + 1][n + 1];
        for (int[] row : dp) Arrays.fill(row, -1);

        int length = lcs(X, Y, m, n, dp);

        System.out.println("====== Result ======");
        System.out.println("Length of Longest Common Subsequence = " + length);
    }
}

""")
def chainmatmul():
    print(r"""
import java.util.*;

public class MatrixChainMultiplicationDP {
    static int matrixChainOrder(int[] p, int i, int j, int[][] dp) {
        if (i == j) return 0;
        if (dp[i][j] != -1) return dp[i][j];

        dp[i][j] = Integer.MAX_VALUE;
        for (int k = i; k < j; k++) {
            int cost = matrixChainOrder(p, i, k, dp)
                     + matrixChainOrder(p, k + 1, j, dp)
                     + p[i - 1] * p[k] * p[j];
            dp[i][j] = Math.min(dp[i][j], cost);
        }
        return dp[i][j];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Matrix Chain Multiplication using Dynamic Programming ======");
        System.out.print("Enter number of matrices: ");
        int n = sc.nextInt();

        int[] p = new int[n + 1];
        System.out.println("====== Enter dimensions ======");
        System.out.println("For n matrices, enter n+1 dimensions (e.g., A1: p0 x p1, A2: p1 x p2, ...)");
        for (int i = 0; i <= n; i++) {
            System.out.print("p" + i + ": ");
            p[i] = sc.nextInt();
        }

        int[][] dp = new int[n + 1][n + 1];
        for (int[] row : dp) Arrays.fill(row, -1);

        int minCost = matrixChainOrder(p, 1, n, dp);

        System.out.println("====== Result ======");
        System.out.println("Minimum number of multiplications required = " + minCost);
    }
}

""")
def floyd():
    print(r"""
import java.util.*;

public class FloydWarshall {
    static final int INF = 99999;

    static void floydWarshall(int[][] graph, int n) {
        int[][] dist = new int[n][n];

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                dist[i][j] = graph[i][j];

        for (int k = 0; k < n; k++) {
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    if (dist[i][k] + dist[k][j] < dist[i][j])
                        dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }

        System.out.println("====== All Pair Shortest Paths (Floyd’s Algorithm) ======");
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (dist[i][j] == INF)
                    System.out.print("INF ");
                else
                    System.out.print(dist[i][j] + " ");
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== All Pair Shortest Path – Floyd’s Algorithm ======");
        System.out.print("Enter number of vertices: ");
        int n = sc.nextInt();

        int[][] graph = new int[n][n];
        System.out.println("Enter adjacency matrix (use 99999 for no direct edge):");
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                graph[i][j] = sc.nextInt();
            }
        }

        floydWarshall(graph, n);
    }
}

""")
def nqueen():
    print(r"""
import java.util.*;

public class NQueens {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== N-Queens Problem ======");
        System.out.print("Enter the number of queens (N): ");
        int n = sc.nextInt();

        int[][] board = new int[n][n];

        System.out.println("====== Solution ======");
        if (placeQueens(board, 0, n)) {
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    System.out.print(board[i][j] == 1 ? "Q " : ". ");
                }
                System.out.println();
            }
        } else {
            System.out.println("No solution exists for N = " + n);
        }
    }

    static boolean placeQueens(int[][] board, int col, int n) {
        if (col >= n) return true;

        for (int row = 0; row < n; row++) {
            if (isSafe(board, row, col, n)) {
                board[row][col] = 1;
                if (placeQueens(board, col + 1, n)) return true;
                board[row][col] = 0;
            }
        }
        return false;
    }

    static boolean isSafe(int[][] board, int row, int col, int n) {
        for (int i = 0; i < col; i++)
            if (board[row][i] == 1)
                return false;

        for (int i = row, j = col; i >= 0 && j >= 0; i--, j--)
            if (board[i][j] == 1)
                return false;

        for (int i = row, j = col; i < n && j >= 0; i++, j--)
            if (board[i][j] == 1)
                return false;

        return true;
    }
}

""")    
def longestpalindrom():
    print(r"""
import java.util.*;

public class LongestPalindromeSubsequence {
    public static int longestPalindromeSubseq(String s) {
        int n = s.length();
        int[][] dp = new int[n][n];
        return solve(s, 0, n - 1, dp);
    }

    public static int solve(String s, int i, int j, int[][] dp) {
        if (i > j) return 0;
        if (i == j) return 1;
        if (dp[i][j] != 0) return dp[i][j];

        if (s.charAt(i) == s.charAt(j))
            dp[i][j] = 2 + solve(s, i + 1, j - 1, dp);
        else
            dp[i][j] = Math.max(solve(s, i, j - 1, dp), solve(s, i + 1, j, dp));

        return dp[i][j];
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("====== Longest Palindromic Subsequence ======");
        System.out.print("Enter a string: ");
        String s = sc.nextLine();

        int result = longestPalindromeSubseq(s);

        System.out.println("====== Result ======");
        System.out.println("Length of the Longest Palindromic Subsequence = " + result);
    }
}

""")
def mergesort():
    print(r"""
import java.util.Scanner;

public class MergeSortProgram {

    // Function to merge two halves
    public static void merge(int[] arr, int left, int mid, int right) {
        int n1 = mid - left + 1;
        int n2 = right - mid;

        int[] L = new int[n1];
        int[] R = new int[n2];

        
        for (int i = 0; i < n1; ++i)
            L[i] = arr[left + i];
        for (int j = 0; j < n2; ++j)
            R[j] = arr[mid + 1 + j];

        
        int i = 0, j = 0;
        int k = left;

        while (i < n1 && j < n2) {
            if (L[i] <= R[j]) {
                arr[k] = L[i];
                i++;
            } else {
                arr[k] = R[j];
                j++;
            }
            k++;
        }

        
        while (i < n1) {
            arr[k] = L[i];
            i++;
            k++;
        }
        while (j < n2) {
            arr[k] = R[j];
            j++;
            k++;
        }
    }

    public static void mergeSort(int[] arr, int left, int right) {
        if (left < right) {
            int mid = left + (right - left) / 2;

            mergeSort(arr, left, mid);
            mergeSort(arr, mid + 1, right);

            merge(arr, left, mid, right);
        }
    }

    
    public static void displayArray(int[] arr) {
        for (int value : arr) {
            System.out.print(value + " ");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("==========================================");
        System.out.println("           MERGE SORT PROGRAM");
        System.out.println("==========================================");

        System.out.print("Enter the number of elements in the array: ");
        int n = sc.nextInt();

        int[] arr = new int[n];
        System.out.println("==========================================");
        System.out.println("Please enter the elements separated by space:");
        for (int i = 0; i < n; i++) {
            arr[i] = sc.nextInt();
        }

        System.out.println("==========================================");
        System.out.println("Unsorted Array:");
        displayArray(arr);

        mergeSort(arr, 0, n - 1);

        System.out.println("==========================================");
        System.out.println("Sorted Array (Using Merge Sort):");
        displayArray(arr);
        System.out.println("==========================================");

        sc.close();
    }
}

""")
def quicksort():
    print(r"""
import java.util.Scanner;

public class QuickSortProgram {
    public static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int p = partition(arr, low, high);
            quickSort(arr, low, p - 1);
            quickSort(arr, p + 1, high);
        }
    }

    public static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        return i + 1;
    }

    public static void displayArray(int[] arr) {
        for (int value : arr) {
            System.out.print(value + " ");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("==========================================");
        System.out.println("           QUICK SORT PROGRAM");
        System.out.println("==========================================");

        System.out.print("Enter the number of elements in the array: ");
        int n = sc.nextInt();

        int[] arr = new int[n];
        System.out.println("==========================================");
        System.out.println("Please enter the elements separated by space:");
        for (int i = 0; i < n; i++) {
            arr[i] = sc.nextInt();
        }

        System.out.println("==========================================");
        System.out.println("Unsorted Array:");
        displayArray(arr);

        quickSort(arr, 0, n - 1);

        System.out.println("==========================================");
        System.out.println("Sorted Array (Using Quick Sort):");
        displayArray(arr);
        System.out.println("==========================================");

        sc.close();
    }
}

""")
def heapsort():
    print(r"""
import java.util.Scanner;

public class HeapSortProgram {
    public static void heapSort(int[] arr) {
        int n = arr.length;
        for (int i = n / 2 - 1; i >= 0; i--) {
            heapify(arr, n, i);
        }
        for (int i = n - 1; i >= 0; i--) {
            int temp = arr[0];
            arr[0] = arr[i];
            arr[i] = temp;
            heapify(arr, i, 0);
        }
    }

    public static void heapify(int[] arr, int n, int i) {
        int largest = i;
        int left = 2 * i + 1;
        int right = 2 * i + 2;
        if (left < n && arr[left] > arr[largest]) largest = left;
        if (right < n && arr[right] > arr[largest]) largest = right;
        if (largest != i) {
            int swap = arr[i];
            arr[i] = arr[largest];
            arr[largest] = swap;
            heapify(arr, n, largest);
        }
    }

    public static void displayArray(int[] arr) {
        for (int value : arr) {
            System.out.print(value + " ");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("==========================================");
        System.out.println("              HEAP SORT PROGRAM");
        System.out.println("==========================================");

        System.out.print("Enter the number of elements in the array: ");
        int n = sc.nextInt();

        int[] arr = new int[n];
        System.out.println("==========================================");
        System.out.println("Please enter the elements separated by space:");
        for (int i = 0; i < n; i++) {
            arr[i] = sc.nextInt();
        }

        System.out.println("==========================================");
        System.out.println("Unsorted Array:");
        displayArray(arr);

        heapSort(arr);

        System.out.println("==========================================");
        System.out.println("Sorted Array (Using Heap Sort):");
        displayArray(arr);
        System.out.println("==========================================");

        sc.close();
    }
}

""")
def pairsort():
    print(r"""
import java.util.*;

public class MergeSortPairs {

    // Comparison function for pairs
    static boolean comparePairs(int[] a, int[] b) {
        if (a[0] < b[0]) return true;
        if (a[0] == b[0] && a[1] < b[1]) return true;
        return false;
    }

    // Merge function
    static void merge(List<int[]> arr, int left, int mid, int right) {
        int n1 = mid - left + 1;
        int n2 = right - mid;

        List<int[]> L = new ArrayList<>();
        List<int[]> R = new ArrayList<>();

        for (int i = 0; i < n1; i++)
            L.add(arr.get(left + i));
        for (int j = 0; j < n2; j++)
            R.add(arr.get(mid + 1 + j));

        int i = 0, j = 0, k = left;

        while (i < n1 && j < n2) {
            if (comparePairs(L.get(i), R.get(j))) {
                arr.set(k, L.get(i));
                i++;
            } else {
                arr.set(k, R.get(j));
                j++;
            }
            k++;
        }

        // Copy remaining elements
        while (i < n1) {
            arr.set(k, L.get(i));
            i++;
            k++;
        }
        while (j < n2) {
            arr.set(k, R.get(j));
            j++;
            k++;
        }
    }

    // Recursive merge sort
    static void mergeSort(List<int[]> arr, int left, int right) {
        if (left < right) {
            int mid = left + (right - left) / 2;

            mergeSort(arr, left, mid);
            mergeSort(arr, mid + 1, right);

            merge(arr, left, mid, right);
        }
    }

    public static void main(String[] args) {
        List<int[]> v = new ArrayList<>();
        v.add(new int[]{3, 5});
        v.add(new int[]{1, 2});
        v.add(new int[]{3, 1});
        v.add(new int[]{2, 8});
        v.add(new int[]{1, 1});

        mergeSort(v, 0, v.size() - 1);

        System.out.println("Sorted pairs:");
        for (int[] p : v) {
            System.out.print("(" + p[0] + ", " + p[1] + ") ");
        }
        System.out.println();
    }
}
""")
def sttarsanmulti():
    print(r"""
import java.util.Scanner;

public class StrassenMatrixMultiplication {
    public static int[][] add(int[][] A, int[][] B) {
        int n = A.length;
        int[][] C = new int[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                C[i][j] = A[i][j] + B[i][j];
        return C;
    }

    public static int[][] subtract(int[][] A, int[][] B) {
        int n = A.length;
        int[][] C = new int[n][n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                C[i][j] = A[i][j] - B[i][j];
        return C;
    }

    public static int[][] strassen(int[][] A, int[][] B) {
        int n = A.length;
        if (n == 1) {
            int[][] C = new int[1][1];
            C[0][0] = A[0][0] * B[0][0];
            return C;
        }

        int newSize = n / 2;
        int[][] A11 = new int[newSize][newSize];
        int[][] A12 = new int[newSize][newSize];
        int[][] A21 = new int[newSize][newSize];
        int[][] A22 = new int[newSize][newSize];
        int[][] B11 = new int[newSize][newSize];
        int[][] B12 = new int[newSize][newSize];
        int[][] B21 = new int[newSize][newSize];
        int[][] B22 = new int[newSize][newSize];

        for (int i = 0; i < newSize; i++) {
            for (int j = 0; j < newSize; j++) {
                A11[i][j] = A[i][j];
                A12[i][j] = A[i][j + newSize];
                A21[i][j] = A[i + newSize][j];
                A22[i][j] = A[i + newSize][j + newSize];

                B11[i][j] = B[i][j];
                B12[i][j] = B[i][j + newSize];
                B21[i][j] = B[i + newSize][j];
                B22[i][j] = B[i + newSize][j + newSize];
            }
        }

        int[][] P1 = strassen(add(A11, A22), add(B11, B22));
        int[][] P2 = strassen(add(A21, A22), B11);
        int[][] P3 = strassen(A11, subtract(B12, B22));
        int[][] P4 = strassen(A22, subtract(B21, B11));
        int[][] P5 = strassen(add(A11, A12), B22);
        int[][] P6 = strassen(subtract(A21, A11), add(B11, B12));
        int[][] P7 = strassen(subtract(A12, A22), add(B21, B22));

        int[][] C11 = add(subtract(add(P1, P4), P5), P7);
        int[][] C12 = add(P3, P5);
        int[][] C21 = add(P2, P4);
        int[][] C22 = add(subtract(add(P1, P3), P2), P6);

        int[][] C = new int[n][n];
        for (int i = 0; i < newSize; i++) {
            for (int j = 0; j < newSize; j++) {
                C[i][j] = C11[i][j];
                C[i][j + newSize] = C12[i][j];
                C[i + newSize][j] = C21[i][j];
                C[i + newSize][j + newSize] = C22[i][j];
            }
        }
        return C;
    }

    public static void displayMatrix(int[][] M) {
        for (int[] row : M) {
            for (int val : row) {
                System.out.print(val + " ");
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("==========================================");
        System.out.println("        STRASSEN MATRIX MULTIPLICATION");
        System.out.println("==========================================");

        System.out.print("Enter the size of the square matrix (power of 2): ");
        int n = sc.nextInt();

        int[][] A = new int[n][n];
        int[][] B = new int[n][n];

        System.out.println("==========================================");
        System.out.println("Enter elements of Matrix A:");
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                A[i][j] = sc.nextInt();

        System.out.println("==========================================");
        System.out.println("Enter elements of Matrix B:");
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                B[i][j] = sc.nextInt();

        System.out.println("==========================================");
        System.out.println("Matrix A:");
        displayMatrix(A);

        System.out.println("==========================================");
        System.out.println("Matrix B:");
        displayMatrix(B);

        int[][] result = strassen(A, B);

        System.out.println("==========================================");
        System.out.println("Resultant Matrix (A x B):");
        displayMatrix(result);
        System.out.println("==========================================");

        sc.close();
    }
}

""")
    
def binarytreemaxpathsum():
    print(r"""
class Solution {
    int maxSum = Integer.MIN_VALUE;

    private int helper(TreeNode root) {
        if(root == null) return 0;

        int left = Math.max(0, helper(root.left));
        int right = Math.max(0, helper(root.right));

        maxSum = Math.max(maxSum, left + right + root.val);

        return Math.max(left, right) + root.val;
    }

    public int maxPathSum(TreeNode root) {
        helper(root);
        return maxSum;
    }
}
""")


def maximumscorewordsformedbyletters():
    print(r"""
public class Solution {
    public int maxScoreWords(String[] words, char[] letters, int[] score) {
        int[] count = new int[26];
        int[] lettersCount = new int[26];
        
        for (char c : letters) {
            count[c - 'a']++;
        }
        
        int ans = 0;
        ans = backtracking(words, score, count, lettersCount, 0, 0, ans);
        return ans;
    }
    
    private int backtracking(String[] words, int[] score, int[] count, int[] lettersCount, int pos, int temp, int ans) {
        for (int i = 0; i < 26; i++) {
            if (lettersCount[i] > count[i]) return ans;
        }
        
        ans = Math.max(ans, temp);
        
        for (int i = pos; i < words.length; i++) {
            for (char c : words[i].toCharArray()) {
                lettersCount[c - 'a']++;
                temp += score[c - 'a'];
            }
            
            ans = backtracking(words, score, count, lettersCount, i + 1, temp, ans);
            
            for (char c : words[i].toCharArray()) {
                lettersCount[c - 'a']--;
                temp -= score[c - 'a'];
            }
        }
        
        return ans;
    }
}
""")
    
def counthighestscorenodes():
    print(r"""
class Solution {
    public int countHighestScoreNodes(int[] parents) {
        HashMap<Integer, List<Integer>> map = new HashMap<>();
        int n = parents.length;

        for (int i = 0; i < n; i++) {
            map.put(i, new ArrayList<>());
        }

        for (int i = 1; i < n; i++) {
            map.get(parents[i]).add(i);
        }

        int[] count = new int[n];
        int x = 1;
        for (int i = 0; i < n; i++) {
            if (count[i] == 0) {
                x = find_count(i, map, count);
            }
        }

        long max = 0;
        int ans = 0;

        for (int i = 0; i < n; i++) {
            List<Integer> child = map.get(i);
            long curr = 1;

            if (child != null) {
                for (int j = 0; j < child.size(); j++) {
                    curr *= (long) count[child.get(j)];
                }
            }

            if (parents[i] != -1) {
                curr *= (long) (n - count[i]);
            }

            if (curr > max) {
                max = curr;
                ans = 1;
            } else if (curr == max) {
                ans++;
            }
        }

        return ans;
    }

    public int find_count(int node, HashMap<Integer, List<Integer>> map, int[] count) {
        if (count[node] != 0) return count[node];

        List<Integer> child = map.get(node);

        if (child == null) {
            return count[node] = 1;
        }

        int cnt = 1;
        for (int i = 0; i < child.size(); i++) {
            cnt = cnt + find_count(child.get(i), map, count);
        }

        count[node] = cnt;
        return cnt;
    }
}
""")
    
def meetingroom3():
    print(r"""
class Solution {
    public int mostBooked(int n, int[][] meetings) {
        long[] roomAvailabilityTime = new long[n];
        int[] meetingCount = new int[n];
        Arrays.sort(meetings, (a, b) -> Integer.compare(a[0], b[0]));

        for (int[] meeting : meetings) {
            int start = meeting[0], end = meeting[1];
            long minRoomAvailabilityTime = Long.MAX_VALUE;
            int minAvailableTimeRoom = 0;
            boolean foundUnusedRoom = false;

            for (int i = 0; i < n; i++) {
                if (roomAvailabilityTime[i] <= start) {
                    foundUnusedRoom = true;
                    meetingCount[i]++;
                    roomAvailabilityTime[i] = end;
                    break;
                }

                if (minRoomAvailabilityTime > roomAvailabilityTime[i]) {
                    minRoomAvailabilityTime = roomAvailabilityTime[i];
                    minAvailableTimeRoom = i;
                }
            }

            if (!foundUnusedRoom) {
                roomAvailabilityTime[minAvailableTimeRoom] += end - start;
                meetingCount[minAvailableTimeRoom]++;
            }
        }

        int maxMeetingCount = 0, maxMeetingCountRoom = 0;
        for (int i = 0; i < n; i++) {
            if (meetingCount[i] > maxMeetingCount) {
                maxMeetingCount = meetingCount[i];
                maxMeetingCountRoom = i;
            }
        }

        return maxMeetingCountRoom;
    }
}
""")

def maxtaxiearnings():
    print(r"""
class Solution {
    public long maxTaxiEarnings(int n, int[][] rides) {
        long ans = 0;
        Arrays.sort(rides, Comparator.comparingDouble(o -> o[0]));

        PriorityQueue<long[]> pq = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));

        for (int[] i : rides) {
            int s = i[0];
            int e = i[1];
            long tip = e - s + i[2];

            while (!pq.isEmpty() && s >= pq.peek()[0]) {
                ans = Math.max(ans, pq.peek()[1]);
                pq.remove();
            }

            pq.add(new long[]{e, tip + ans});
        }

        while (!pq.isEmpty()) {
            ans = Math.max(ans, pq.peek()[1]);
            pq.remove();
        }

        return ans;
    }
}
""")

def reversepairs():
    print(r"""
class Solution {
    static int c = 0;

    static void countPairs(int[] nums, int l, int m, int h) {
        int r = m + 1;

        for (int i = l; i <= m; i++) {
            while (r <= h && (long) nums[i] > (long) 2 * nums[r]) r++;
            c += (r - (m + 1));
        }
    }

    static void mergeSort(int[] nums, int l, int h) {
        if (l < h) {
            int m = l + (h - l) / 2;
            mergeSort(nums, l, m);
            mergeSort(nums, m + 1, h);
            countPairs(nums, l, m, h);
            merge(nums, l, m, h);
        }
    }

    static void merge(int[] nums, int l, int m, int h) {
        int[] temp = new int[h - l + 1];
        int i = l, j = m + 1;
        int k = 0;

        while (i <= m && j <= h) {
            if (nums[i] > nums[j]) {
                temp[k++] = nums[j++];
            } else {
                temp[k++] = nums[i++];
            }
        }

        while (i <= m) {
            temp[k++] = nums[i++];
        }

        while (j <= h) {
            temp[k++] = nums[j++];
        }

        for (int x = 0; x < temp.length; x++) {
            nums[x + l] = temp[x];
        }
    }

    public int reversePairs(int[] nums) {
        c = 0;
        mergeSort(nums, 0, nums.length - 1);
        return c;
    }
}
""")

def superpow():
    print(r"""
class Solution {
    private static final int MOD = 1337;

    private int pow(int a, int b) {
        int result = 1;
        a %= MOD;
        for (int i = 0; i < b; i++) {
            result = (result * a) % MOD;
        }
        return result;
    }

    public int superPow(int a, int[] b) {
        int result = 1;
        for (int i = b.length - 1; i >= 0; i--) {
            result = (result * pow(a, b[i])) % MOD;
            a = pow(a, 10);
        }
        return result;
    }
}
""")

def diffwaystocomputeparanthesis():
    print(r"""
class Solution {
    public List<Integer> diffWaysToCompute(String expression) {
        List<Integer> results = new ArrayList<>();

        if (expression.length() == 0) return results;
        if (expression.length() == 1) {
            results.add(Integer.parseInt(expression));
            return results;
        }
        if (expression.length() == 2 && Character.isDigit(expression.charAt(0))) {
            results.add(Integer.parseInt(expression));
            return results;
        }

        for (int i = 0; i < expression.length(); i++) {
            char currentChar = expression.charAt(i);
            if (Character.isDigit(currentChar)) continue;

            List<Integer> leftResults = diffWaysToCompute(expression.substring(0, i));
            List<Integer> rightResults = diffWaysToCompute(expression.substring(i + 1));

            for (int leftValue : leftResults) {
                for (int rightValue : rightResults) {
                    int computedResult = 0;
                    switch (currentChar) {
                        case '+':
                            computedResult = leftValue + rightValue;
                            break;
                        case '-':
                            computedResult = leftValue - rightValue;
                            break;
                        case '*':
                            computedResult = leftValue * rightValue;
                            break;
                    }
                    results.add(computedResult);
                }
            }
        }
        return results;
    }
}
""")

def reversekgroup():
    print(r"""
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        if (head == null || k == 1) return head;

        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy, curr = head;

        int count = 0;
        while (curr != null) {
            count++;
            curr = curr.next;
        }

        while (count >= k) {
            curr = prev.next;
            ListNode next = curr.next;

            for (int i = 1; i < k; i++) {
                curr.next = next.next;
                next.next = prev.next;
                prev.next = next;
                next = curr.next;
            }

            prev = curr;
            count -= k;
        }

        return dummy.next;
    }
}
""")

def findkthnumberinmultiplicationtable():
    print(r"""
class Solution {
    public boolean enough(int x, int m, int n, int k) {
        int count = 0;
        for (int i = 1; i <= m; i++) {
            count += Math.min(x / i, n);
        }
        return count >= k;
    }

    public int findKthNumber(int m, int n, int k) {
        int lo = 1, hi = m * n;
        while (lo < hi) {
            int mi = lo + (hi - lo) / 2;
            if (!enough(mi, m, n, k)) lo = mi + 1;
            else hi = mi;
        }
        return lo;
    }
}
""")