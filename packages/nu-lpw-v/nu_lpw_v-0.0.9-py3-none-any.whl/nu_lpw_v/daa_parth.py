def code():
    print(r"""
0/1 knapsack
#include <iostream>
using namespace std;

int knapSack(int W, int wt[], int val[], int n) {
    int dp[n + 1][W + 1];

    // Initialize first row and first column
    for (int i = 0; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            if (i == 0 || w == 0)
                dp[i][w] = 0;
            else if (wt[i - 1] <= w)
                dp[i][w] = max(val[i - 1] + dp[i - 1][w - wt[i - 1]], dp[i - 1][w]);
            else
                dp[i][w] = dp[i - 1][w];
        }
    }

    return dp[n][W];
}

int main() {
    int val[] = {60, 100, 120};
    int wt[] = {1, 2, 3};
    int W = 5;
    int n = 3;

    cout << "Maximum Value = " << knapSack(W, wt, val, n);
    return 0;
}

//activation selection

#include <bits/stdc++.h>
using namespace std;

void activitySelection(vector<int> start, vector<int> finish, int n) {
    vector<pair<int,int>> activities;
    for (int i = 0; i < n; i++)
        activities.push_back({finish[i], start[i]});

    sort(activities.begin(), activities.end()); // sort by finish time

    cout << "Selected activities: ";
    int lastFinish = -1;
    for (auto act : activities) {
        if (act.second >= lastFinish) {
            cout << "(" << act.second << "," << act.first << ") ";
            lastFinish = act.first;
        }
    }
}

int main() {
    vector<int> start = {1, 3, 0, 5, 8, 5};
    vector<int> finish = {2, 4, 6, 7, 9, 9};
    int n = start.size();

    activitySelection(start, finish, n);
    return 0;
}

//fractional knapsack
#include <bits/stdc++.h>
using namespace std;

struct Item {
    int value, weight;
};

bool cmp(Item a, Item b) {
    double r1 = (double)a.value / a.weight;
    double r2 = (double)b.value / b.weight;
    return r1 > r2;
}

double fractionalKnapsack(int W, vector<Item>& items, int n) {
    sort(items.begin(), items.end(), cmp);

    double finalValue = 0.0;

    for (int i = 0; i < n; i++) {
        if (items[i].weight <= W) {
            W -= items[i].weight;
            finalValue += items[i].value;
        } else {
            finalValue += items[i].value * ((double)W / items[i].weight);
            break;
        }
    }

    return finalValue;
}

int main() {
    int W = 50;
    vector<Item> items = {{60, 10}, {100, 20}, {120, 30}};
    int n = items.size();

    cout << "Maximum value = " << fractionalKnapsack(W, items, n);
    return 0;
}
//dijastrst algo
#include <bits/stdc++.h>
using namespace std;

void dijkstra(int V, vector<vector<pair<int,int>>>& graph, int src) {
    vector<int> dist(V, INT_MAX);
    dist[src] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<pair<int,int>>> pq;

    pq.push({0, src});

    while (!pq.empty()) {
        int u = pq.top().second;
        int d = pq.top().first;
        pq.pop();

        for (auto edge : graph[u]) {
            int v = edge.first, w = edge.second;
            if (d + w < dist[v]) {
                dist[v] = d + w;
                pq.push({dist[v], v});
            }
        }
    }

    cout << "Vertex\tDistance\n";
    for (int i = 0; i < V; i++)
        cout << i << "\t" << dist[i] << endl;
}

int main() {
    int V = 5;
    vector<vector<pair<int,int>>> graph(V);

    graph[0] = {{1,10},{4,5}};
    graph[1] = {{2,1},{4,2}};
    graph[2] = {{3,4}};
    graph[3] = {{0,7},{2,6}};
    graph[4] = {{1,3},{2,9},{3,2}};

    dijkstra(V, graph, 0);
    return 0;
}

//prims

#include <bits/stdc++.h>
using namespace std;

int minKey(vector<int>& key, vector<bool>& mstSet, int V) {
    int minVal = INT_MAX, minIndex;
    for (int v = 0; v < V; v++)
        if (!mstSet[v] && key[v] < minVal)
            minVal = key[v], minIndex = v;
    return minIndex;
}

void primMST(vector<vector<int>>& graph, int V) {
    vector<int> parent(V, -1), key(V, INT_MAX);
    vector<bool> mstSet(V, false);
    key[0] = 0;

    for (int count = 0; count < V - 1; count++) {
        int u = minKey(key, mstSet, V);
        mstSet[u] = true;

        for (int v = 0; v < V; v++)
            if (graph[u][v] && !mstSet[v] && graph[u][v] < key[v])
                parent[v] = u, key[v] = graph[u][v];
    }

    cout << "Edge \tWeight\n";
    for (int i = 1; i < V; i++)
        cout << parent[i] << " - " << i << "\t" << graph[i][parent[i]] << endl;
}

int main() {
    vector<vector<int>> graph = {
        {0, 2, 0, 6, 0},
        {2, 0, 3, 8, 5},
        {0, 3, 0, 0, 7},
        {6, 8, 0, 0, 9},
        {0, 5, 7, 9, 0}
    };

    primMST(graph, 5);
    return 0;
}
//krushal 

#include <bits/stdc++.h>
using namespace std;

struct Edge {
    int u, v, w;
};

int findParent(int u, vector<int>& parent) {
    if (u == parent[u]) return u;
    return parent[u] = findParent(parent[u], parent);
}

void unionSet(int u, int v, vector<int>& parent, vector<int>& rank) {
    u = findParent(u, parent);
    v = findParent(v, parent);
    if (rank[u] < rank[v]) parent[u] = v;
    else if (rank[v] < rank[u]) parent[v] = u;
    else parent[v] = u, rank[u]++;
}

void kruskalMST(vector<Edge>& edges, int V) {
    sort(edges.begin(), edges.end(), [](Edge a, Edge b){ return a.w < b.w; });
    vector<int> parent(V), rank(V, 0);
    for (int i = 0; i < V; i++) parent[i] = i;

    vector<Edge> result;
    for (auto e : edges) {
        if (findParent(e.u, parent) != findParent(e.v, parent)) {
            result.push_back(e);
            unionSet(e.u, e.v, parent, rank);
        }
    }

    cout << "Edge \tWeight\n";
    for (auto e : result)
        cout << e.u << " - " << e.v << "\t" << e.w << endl;
}

int main() {
    vector<Edge> edges = {
        {0, 1, 10}, {0, 2, 6}, {0, 3, 5}, {1, 3, 15}, {2, 3, 4}
    };
    kruskalMST(edges, 4);
    return 0;
}


//longest consecutive

#include <iostream>
#include <vector>
using namespace std;

int lcs(string X, string Y) {
    int m = X.size(), n = Y.size();
    vector<vector<int>> dp(m + 1, vector<int>(n + 1, 0));

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (X[i - 1] == Y[j - 1])
                dp[i][j] = 1 + dp[i - 1][j - 1];
            else
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
        }
    }

    return dp[m][n];
}

int main() {
    string X = "ABCBDAB", Y = "BDCABA";
    cout << "Length of LCS = " << lcs(X, Y);
    return 0;
}

//mcmm
#include <iostream>
#include <vector>
#include <climits>
using namespace std;

int MCM(int p[], int n) {
    vector<vector<int>> dp(n, vector<int>(n, 0));

    for (int L = 2; L < n; L++) { // chain length
        for (int i = 1; i < n - L + 1; i++) {
            int j = i + L - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; k++) {
                int cost = dp[i][k] + dp[k + 1][j] + p[i - 1] * p[k] * p[j];
                dp[i][j] = min(dp[i][j], cost);
            }
        }
    }

    return dp[1][n - 1];
}

int main() {
    int arr[] = {40, 20, 30, 10, 30};
    int n = 5;
    cout << "Minimum number of multiplications: " << MCM(arr, n);
    return 0;
}

//floyd warshell
#include <bits/stdc++.h>
using namespace std;

#define INF 99999

void floydWarshall(int graph[][4], int V) {
    int dist[V][V];

    // Step 1: Initialize distance matrix
    for (int i = 0; i < V; i++)
        for (int j = 0; j < V; j++)
            dist[i][j] = graph[i][j];

    // Step 2: Update distances considering each vertex as intermediate
    for (int k = 0; k < V; k++) {           // intermediate vertex
        for (int i = 0; i < V; i++) {       // source
            for (int j = 0; j < V; j++) {   // destination
                if (dist[i][k] + dist[k][j] < dist[i][j])
                    dist[i][j] = dist[i][k] + dist[k][j];
            }
        }
    }

    // Step 3: Print final matrix
    cout << "\nShortest distance matrix:\n";
    for (int i = 0; i < V; i++) {
        for (int j = 0; j < V; j++) {
            if (dist[i][j] == INF)
                cout << "INF ";
            else
                cout << dist[i][j] << "   ";
        }
        cout << endl;
    }
}

int main() {
    int V = 4;
    int graph[4][4] = {
        {0, 5, INF, 10},
        {INF, 0, 3, INF},
        {INF, INF, 0, 1},
        {INF, INF, INF, 0}
    };

    floydWarshall(graph, V);
    return 0;
}

//bellaman ford
#include <bits/stdc++.h>
using namespace std;

struct Edge {
    int src, dest, weight;
};

void bellmanFord(int V, int E, vector<Edge>& edges, int src) {
    vector<int> dist(V, INT_MAX);
    dist[src] = 0;

    // Step 1: Relax edges V-1 times
    for (int i = 1; i <= V - 1; i++) {
        for (int j = 0; j < E; j++) {
            int u = edges[j].src;
            int v = edges[j].dest;
            int w = edges[j].weight;

            if (dist[u] != INT_MAX && dist[u] + w < dist[v])
                dist[v] = dist[u] + w;
        }
    }

    // Step 2: Check for negative weight cycles
    for (int j = 0; j < E; j++) {
        int u = edges[j].src;
        int v = edges[j].dest;
        int w = edges[j].weight;

        if (dist[u] != INT_MAX && dist[u] + w < dist[v]) {
            cout << "⚠️ Negative weight cycle detected!";
            return;
        }
    }

    // Step 3: Print distances
    cout << "Vertex\tDistance from Source\n";
    for (int i = 0; i < V; i++)
        cout << i << "\t" << dist[i] << endl;
}

int main() {
    int V = 5;  // vertices
    int E = 8;  // edges
    vector<Edge> edges = {
        {0, 1, -1},
        {0, 2, 4},
        {1, 2, 3},
        {1, 3, 2},
        {1, 4, 2},
        {3, 2, 5},
        {3, 1, 1},
        {4, 3, -3}
    };

    bellmanFord(V, E, edges, 0);
    return 0;
}







#include <iostream>
#include <vector>
#include <string>
#include <algorithm> // For std::sort, std::max, std::min, std::fill
#include <climits>   // For INT_MAX
#include <iomanip>   // For std::setw (optional, for printing)
#include <functional> // For std::function (used in Merge Sort)

// Using declarations for brevity in a single file context
using std::cin;
using std::cout;
using std::endl;
using std::vector;
using std::string;

// --- Function Prototypes ---

// Prototypes for Strassen's
vector<vector<int>> strassen(const vector<vector<int>>& A, const vector<vector<int>>& B);
vector<vector<int>> add(const vector<vector<int>>& A, const vector<vector<int>>& B);
vector<vector<int>> sub(const vector<vector<int>>& A, const vector<vector<int>>& B);

// Struct for Job Sequencing
struct Job {
    char id;
    int deadline, profit;
    Job(char id, int deadline, int profit) : id(id), deadline(deadline), profit(profit) {}
};

// Prototypes for Dijkstra
int minDistance(const vector<int>& dist, const vector<bool>& visited);
void dijkstra(const vector<vector<int>>& graph, int src);

// Prototypes for N-Queens
extern int N_QUEENS_N; // Use extern to declare, will be defined below
void printSolution(const vector<vector<int>>& board);
bool isSafe(const vector<vector<int>>& board, int row, int col);
bool solveNQUtil(vector<vector<int>>& board, int col);
void solveNQ();

// Prototype for Sum of Subsets
void findSubsets(const vector<int>& arr, int index, int sum, int target, string set);

// Prototype for Bellman-Ford
void bellmanFord(const vector<vector<int>>& edges, int V, int E, int src);

// Prototype for Multistage Graph
int shortestPath(const vector<vector<int>>& graph);

// Prototype for Floyd-Warshall
void allPairs(vector<vector<int>>& graph);


// --- Main Function ---
// (The user provided separate main functions; in C++ this is handled
// by commenting/uncommenting the desired function call in main)
int main() {
    // Please uncomment ONE of the following sections to run the
    // corresponding algorithm.

    /*
    // **** Binary Search ****
    cout << "**** Binary Search ****" << endl;
    int n_bs;
    cout << "Enter size: ";
    cin >> n_bs;
    vector<int> arr_bs(n_bs);
    cout << "Enter sorted elements:" << endl;
    for (int i = 0; i < n_bs; i++)
        cin >> arr_bs[i];
    cout << "Enter element to search: ";
    int key_bs;
    cin >> key_bs;
    int low_bs = 0, high_bs = n_bs - 1, mid_bs;
    bool flag_bs = false;
    while (low_bs <= high_bs) {
        mid_bs = low_bs + (high_bs - low_bs) / 2; // Avoid overflow
        if (arr_bs[mid_bs] == key_bs) {
            cout << "Found at index " << mid_bs << endl;
            flag_bs = true;
            break;
        } else if (arr_bs[mid_bs] < key_bs)
            low_bs = mid_bs + 1;
        else
            high_bs = mid_bs - 1;
    }
    if (!flag_bs) cout << "Not found" << endl;
    */

    /*
    // ****** min-max *******
    cout << "\n****** Min-Max *******" << endl;
    int n_mm;
    cout << "Enter number of elements: ";
    cin >> n_mm;
    vector<int> arr_mm(n_mm);
    cout << "Enter elements:" << endl;
    for (int i = 0; i < n_mm; i++)
        cin >> arr_mm[i];

    if (n_mm > 0) {
        int min_mm = arr_mm[0], max_mm = arr_mm[0];
        for (int i = 1; i < n_mm; i++) {
            if (arr_mm[i] < min_mm)
                min_mm = arr_mm[i];
            if (arr_mm[i] > max_mm)
                max_mm = arr_mm[i];
        }
        cout << "Minimum: " << min_mm << endl;
        cout << "Maximum: " << max_mm << endl;
    } else {
        cout << "No elements entered." << endl;
    }
    */
    
    /*
    // ******** Merge Sort *********
    cout << "\n******** Merge Sort *********" << endl;
    cout << "Enter number of elements: ";
    int n_ms;
    cin >> n_ms;
    vector<int> arr_ms(n_s);
    cout << "Enter elements: " << endl;
    for (int i = 0; i < n_ms; i++) cin >> arr_ms[i];

    // Lambda function for merge
    auto merge = [](vector<int>& arr, int l, int m, int r) {
        vector<int> temp(r - l + 1);
        int i = l, j = m + 1, k = 0;
        while (i <= m && j <= r) temp[k++] = (arr[i] <= arr[j]) ? arr[i++] : arr[j++];
        while (i <= m) temp[k++] = arr[i++];
        while (j <= r) temp[k++] = arr[j++];
        for (i = l, k = 0; i <= r; i++, k++) arr[i] = temp[k];
    };

    // Lambda function for mergeSort (must capture merge)
    // We need std::function to declare a recursive lambda
    std::function<void(vector<int>&, int, int)> mergeSort = 
        [&](vector<int>& arr, int l, int r) {
        if (l < r) {
            int m = l + (r - l) / 2;
            mergeSort(arr, l, m);
            mergeSort(arr, m + 1, r);
            merge(arr, l, m, r);
        }
    };

    mergeSort(arr_ms, 0, n_ms - 1);

    cout << "Sorted array: ";
    for (int num : arr_ms) cout << num << " ";
    cout << endl;
    */

    /*
    // **************** Quick Sort ************
    cout << "\n**************** Quick Sort ************" << endl;
    
    // Lambda for partition
    auto partition = [](vector<int>& arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;
        for (int j = low; j < high; j++) {
            if (arr[j] < pivot) {
                i++;
                std::swap(arr[i], arr[j]);
            }
        }
        std::swap(arr[i + 1], arr[high]);
        return i + 1;
    };

    // Recursive lambda for quickSort
    std::function<void(vector<int>&, int, int)> quickSort = 
        [&](vector<int>& arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    };

    vector<int> arr_qs = {9, 4, 6, 2, 7};
    cout << "Original array: 9 4 6 2 7" << endl;
    quickSort(arr_qs, 0, arr_qs.size() - 1);
    cout << "Sorted array: ";
    for (int num : arr_qs)
        cout << num << " ";
    cout << endl;
    */

    /*
    // ************** Strassen’s Matrix Multiplication **********
    cout << "\n************** Strassen’s Matrix Multiplication **********" << endl;
    int n_sm;
    cout << "Enter size (n x n, power of 2): ";
    cin >> n_sm;
    vector<vector<int>> A_sm(n_sm, vector<int>(n_sm));
    vector<vector<int>> B_sm(n_sm, vector<int>(n_sm));

    cout << "Enter matrix A:" << endl;
    for (int i = 0; i < n_sm; i++)
        for (int j = 0; j < n_sm; j++)
            cin >> A_sm[i][j];

    cout << "Enter matrix B:" << endl;
    for (int i = 0; i < n_sm; i++)
        for (int j = 0; j < n_sm; j++)
            cin >> B_sm[i][j];

    vector<vector<int>> C_sm = strassen(A_sm, B_sm);

    cout << "Resultant Matrix:" << endl;
    for (const auto& row : C_sm) {
        for (int val : row)
            cout << val << " ";
        cout << endl;
    }
    */

    /*
    // *************** knapsack *************
    cout << "\n*************** Knapsack *************" << endl;
    cout << "Enter number of items: ";
    int n_ks;
    cin >> n_ks;
    vector<int> w_ks(n_ks), v_ks(n_ks);
    cout << "Enter weights: ";
    for (int i = 0; i < n_ks; i++) cin >> w_ks[i];
    cout << "Enter values: ";
    for (int i = 0; i < n_ks; i++) cin >> v_ks[i];
    cout << "Enter knapsack capacity (W): ";
    int W_ks;
    cin >> W_ks;

    vector<vector<int>> dp_ks(n_ks + 1, vector<int>(W_ks + 1, 0));
    for (int i = 1; i <= n_ks; i++)
        for (int j = 1; j <= W_ks; j++)
            dp_ks[i][j] = (w_ks[i - 1] <= j) ? 
                std::max(v_ks[i - 1] + dp_ks[i - 1][j - w_ks[i - 1]], dp_ks[i - 1][j]) : 
                dp_ks[i - 1][j];

    cout << "Maximum value: " << dp_ks[n_ks][W_ks] << endl;
    */

    /*
    // *************** job sequence ****************
    cout << "\n*************** Job Sequencing ****************" << endl;
    vector<Job> jobs_js = {
        Job('a', 2, 100),
        Job('b', 1, 19),
        Job('c', 2, 27),
        Job('d', 1, 25),
        Job('e', 3, 15)
    };
    
    // Sort jobs in decreasing order of profit
    std::sort(jobs_js.begin(), jobs_js.end(), [](const Job& a, const Job& b) {
        return a.profit > b.profit;
    });

    int n_js = jobs_js.size();
    int max_deadline = 0;
    for(const auto& job : jobs_js) {
        max_deadline = std::max(max_deadline, job.deadline);
    }
    
    // Use max_deadline for slot size
    vector<bool> slot_js(max_deadline, false);
    vector<char> result_js(max_deadline, 0); // 0 indicates empty slot

    for (int i = 0; i < n_js; i++) {
        // Start from the job's deadline and find an empty slot backwards
        for (int j = std::min(max_deadline, jobs_js[i].deadline) - 1; j >= 0; j--) {
            if (!slot_js[j]) {
                result_js[j] = jobs_js[i].id;
                slot_js[j] = true;
                break;
            }
        }
    }

    cout << "Scheduled jobs: ";
    for (char c : result_js)
        if (c != 0)
            cout << c << " ";
    cout << endl;
    */
    
    /*
    // ***************** dijikarts ********
    cout << "\n***************** Dijkstra ****************" << endl;
    int V_dj;
    cout << "Enter number of vertices: ";
    cin >> V_dj;
    vector<vector<int>> graph_dj(V_dj, vector<int>(V_dj));

    cout << "Enter adjacency matrix (0 if no edge):" << endl;
    for (int i = 0; i < V_dj; i++)
        for (int j = 0; j < V_dj; j++)
            cin >> graph_dj[i][j];

    cout << "Enter source vertex: ";
    int src_dj;
    cin >> src_dj;

    dijkstra(graph_dj, src_dj);
    */

    /*
    // ************ N-Queens ***********
    cout << "\n************ N-Queens (N=4) ***********" << endl;
    solveNQ();
    */

    /*
    // ****************** sum of subsets *************
    cout << "\n****************** Sum of Subsets *************" << endl;
    vector<int> arr_ss = {10, 7, 5, 18, 12, 20, 15};
    int target_ss = 35;
    cout << "Subsets with sum " << target_ss << ":" << endl;
    findSubsets(arr_ss, 0, 0, target_ss, "");
    */
    
    /*
    // ***************** bellman-ford *************
    cout << "\n***************** Bellman-Ford *************" << endl;
    int V_bf = 5, E_bf = 8;
    // Store edges as {u, v, w}
    vector<vector<int>> edges_bf = {
        {0, 1, -1},
        {0, 2, 4},
        {1, 2, 3},
        {1, 3, 2},
        {1, 4, 2},
        {3, 2, 5},
        {3, 1, 1},
        {4, 3, -3}
    };
    bellmanFord(edges_bf, V_bf, E_bf, 0);
    */

    /*
    // ******************** MultistageGraph *************
    cout << "\n******************** Multistage Graph *************" << endl;
    int INF_mg = 999; // Using 999 as INF, as in the Java example
    vector<vector<int>> graph_mg = {
        { 0, 9, 7, 3, 2, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg },
        { INF_mg, 0, INF_mg, INF_mg, INF_mg, 4, 2, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg },
        { INF_mg, INF_mg, 0, INF_mg, INF_mg, 1, 3, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg },
        { INF_mg, INF_mg, INF_mg, 0, INF_mg, INF_mg, 11, 11, INF_mg, INF_mg, INF_mg, INF_mg },
        { INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, 7, 8, INF_mg, INF_mg, INF_mg, INF_mg },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, INF_mg, 6, 5, INF_mg, INF_mg },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, 4, 3, INF_mg, INF_mg },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, INF_mg, 6, INF_mg },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, INF_mg, 4 },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, INF_mg, 2 },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0, 5 },
        { INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, INF_mg, 0 }
    };

    cout << "Shortest path cost: " << shortestPath(graph_mg) << endl;
    */

    
    // **************** Floyd-Warshall (All-Pairs Shortest Path) *********
    cout << "\n**************** Floyd-Warshall (All-Pairs) ************" << endl;
    int INF_fw = INT_MAX; // Use INT_MAX for infinity
    vector<vector<int>> graph_fw = {
        {0, 4, 1},
        {6, 0, 2},
        {3, INF_fw, 0}
    };

    allPairs(graph_fw);

    cout << "All-pairs shortest path matrix:" << endl;
    for (int i = 0; i < graph_fw.size(); i++) {
        for (int j = 0; j < graph_fw[i].size(); j++) {
            if (graph_fw[i][j] == INF_fw)
                cout << "INF ";
            else
                cout << graph_fw[i][j] << "   ";
        }
        cout << endl;
    }
    

    return 0; // End of main
}

// --- Function Implementations ---

// ****** Strassen’s Matrix Multiplication ******
vector<vector<int>> add(const vector<vector<int>>& A, const vector<vector<int>>& B) {
    int n = A.size();
    vector<vector<int>> C(n, vector<int>(n));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = A[i][j] + B[i][j];
    return C;
}

vector<vector<int>> sub(const vector<vector<int>>& A, const vector<vector<int>>& B) {
    int n = A.size();
    vector<vector<int>> C(n, vector<int>(n));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = A[i][j] - B[i][j];
    return C;
}

vector<vector<int>> strassen(const vector<vector<int>>& A, const vector<vector<int>>& B) {
    int n = A.size();
    vector<vector<int>> C(n, vector<int>(n));

    if (n == 1) {
        C[0][0] = A[0][0] * B[0][0];
    } else {
        int k = n / 2;
        vector<vector<int>> a11(k, vector<int>(k)), a12(k, vector<int>(k)), a21(k, vector<int>(k)), a22(k, vector<int>(k));
        vector<vector<int>> b11(k, vector<int>(k)), b12(k, vector<int>(k)), b21(k, vector<int>(k)), b22(k, vector<int>(k));

        for (int i = 0; i < k; i++)
            for (int j = 0; j < k; j++) {
                a11[i][j] = A[i][j];
                a12[i][j] = A[i][j + k];
                a21[i][j] = A[i + k][j];
                a22[i][j] = A[i + k][j + k];
                b11[i][j] = B[i][j];
                b12[i][j] = B[i][j + k];
                b21[i][j] = B[i + k][j];
                b22[i][j] = B[i + k][j + k];
            }

        vector<vector<int>> p1 = strassen(add(a11, a22), add(b11, b22));
        vector<vector<int>> p2 = strassen(add(a21, a22), b11);
        vector<vector<int>> p3 = strassen(a11, sub(b12, b22));
        vector<vector<int>> p4 = strassen(a22, sub(b21, b11));
        vector<vector<int>> p5 = strassen(add(a11, a12), b22);
        vector<vector<int>> p6 = strassen(sub(a21, a11), add(b11, b12));
        vector<vector<int>> p7 = strassen(sub(a12, a22), add(b21, b22));

        vector<vector<int>> c11 = add(sub(add(p1, p4), p5), p7);
        vector<vector<int>> c12 = add(p3, p5);
        vector<vector<int>> c21 = add(p2, p4);
        vector<vector<int>> c22 = add(sub(add(p1, p3), p2), p6);

        for (int i = 0; i < k; i++)
            for (int j = 0; j < k; j++) {
                C[i][j] = c11[i][j];
                C[i][j + k] = c12[i][j];
                C[i + k][j] = c21[i][j];
                C[i + k][j + k] = c22[i][j];
            }
    }
    return C;
}

// ****** Dijkstra ******
int minDistance(const vector<int>& dist, const vector<bool>& visited) {
    int min = INT_MAX, minIndex = -1;
    for (int i = 0; i < dist.size(); i++) {
        if (!visited[i] && dist[i] <= min) {
            min = dist[i];
            minIndex = i;
        }
    }
    return minIndex;
}

void dijkstra(const vector<vector<int>>& graph, int src) {
    int V = graph.size();
    vector<int> dist(V);
    vector<bool> visited(V);

    std::fill(dist.begin(), dist.end(), INT_MAX);
    std::fill(visited.begin(), visited.end(), false);
    dist[src] = 0;

    for (int count = 0; count < V - 1; count++) {
        int u = minDistance(dist, visited);
        if (u == -1) break; // No path or all reachable nodes visited
        visited[u] = true;

        for (int v = 0; v < V; v++) {
            if (!visited[v] && graph[u][v] != 0 &&
                dist[u] != INT_MAX && // Check for overflow
                dist[u] + graph[u][v] < dist[v]) {
                dist[v] = dist[u] + graph[u][v];
            }
        }
    }

    cout << "Vertex\tDistance from Source" << endl;
    for (int i = 0; i < V; i++)
        cout << i << "\t\t" << (dist[i] == INT_MAX ? "INF" : std::to_string(dist[i])) << endl;
}

// ****** N-Queens **********
int N_QUEENS_N = 4; // Definition of the global variable

void printSolution(const vector<vector<int>>& board) {
    for (int i = 0; i < N_QUEENS_N; i++) {
        for (int j = 0; j < N_QUEENS_N; j++)
            cout << board[i][j] << " ";
        cout << endl;
    }
    cout << endl;
}

bool isSafe(const vector<vector<int>>& board, int row, int col) {
    for (int i = 0; i < col; i++)
        if (board[row][i] == 1) return false;

    for (int i = row, j = col; i >= 0 && j >= 0; i--, j--)
        if (board[i][j] == 1) return false;

    for (int i = row, j = col; i < N_QUEENS_N && j >= 0; i++, j--)
        if (board[i][j] == 1) return false;

    return true;
}

bool solveNQUtil(vector<vector<int>>& board, int col) {
    if (col >= N_QUEENS_N) return true;

    for (int i = 0; i < N_QUEENS_N; i++) {
        if (isSafe(board, i, col)) {
            board[i][col] = 1;

            if (solveNQUtil(board, col + 1))
                return true;

            board[i][col] = 0; // Backtrack
        }
    }
    return false;
}

void solveNQ() {
    vector<vector<int>> board(N_QUEENS_N, vector<int>(N_QUEENS_N, 0));

    if (!solveNQUtil(board, 0)) {
        cout << "No solution exists" << endl;
        return;
    }

    printSolution(board);
}

// ****** Sum of Subsets **********
void findSubsets(const vector<int>& arr, int index, int sum, int target, string set) {
    if (sum == target) {
        cout << set << endl;
        return;
    }
    if (index == arr.size() || sum > target) return;

    // Include current element
    findSubsets(arr, index + 1, sum + arr[index], target, set + std::to_string(arr[index]) + " ");
    // Exclude current element
    findSubsets(arr, index + 1, sum, target, set);
}

// ****** Bellman-Ford **********
void bellmanFord(const vector<vector<int>>& edges, int V, int E, int src) {
    vector<int> dist(V, INT_MAX);
    dist[src] = 0;

    for (int i = 1; i < V; i++) {
        for (int j = 0; j < E; j++) {
            int u = edges[j][0], v = edges[j][1], w = edges[j][2];
            if (dist[u] != INT_MAX && dist[u] + w < dist[v])
                dist[v] = dist[u] + w;
        }
    }

    // Check for negative-weight cycles
    for (int j = 0; j < E; j++) {
        int u = edges[j][0], v = edges[j][1], w = edges[j][2];
        if (dist[u] != INT_MAX && dist[u] + w < dist[v]) {
            cout << "Graph contains negative weight cycle" << endl;
            return; // Or handle as needed
        }
    }

    for (int i = 0; i < V; i++)
        cout << "Vertex " << i << " Distance from Source: " << (dist[i] == INT_MAX ? "INF" : std::to_string(dist[i])) << endl;
}

// ****** Multistage Graph **********
int shortestPath(const vector<vector<int>>& graph) {
    int n = graph.size();
    vector<int> dist(n);
    dist[n - 1] = 0;
    int INF_mg = 999; // Local INF as per example

    for (int i = n - 2; i >= 0; i--) {
        dist[i] = INT_MAX; // Use INT_MAX for internal logic
        for (int j = i + 1; j < n; j++) {
            if (graph[i][j] != 0 && graph[i][j] != INF_mg && dist[j] != INT_MAX) {
                 if (dist[j] + graph[i][j] < dist[i]) {
                    dist[i] = dist[j] + graph[i][j];
                 }
            }
        }
    }
    return dist[0];
}

// ****** Floyd-Warshall **********
void allPairs(vector<vector<int>>& graph) {
    int v = graph.size();
    int INF = INT_MAX; // Local INF

    for (int k = 0; k < v; k++) {
        for (int i = 0; i < v; i++) {
            for (int j = 0; j < v; j++) {
                if (graph[i][k] != INF && graph[k][j] != INF) {
                    graph[i][j] = std::min(graph[i][j], graph[i][k] + graph[k][j]);
                }
            }
        }
    }
}


| **Topic**                 | **Algorithm / Concept**                   | **Time Complexity**     | **Space Complexity** | **Notes / Key Idea**               |
| ------------------------- | ----------------------------------------- | ----------------------- | -------------------- | ---------------------------------- |
| **Sorting**               | **Bubble Sort**                           | O(n²)                   | O(1)                 | Repeatedly swap adjacent elements  |
|                           | **Selection Sort**                        | O(n²)                   | O(1)                 | Select min element each pass       |
|                           | **Insertion Sort**                        | O(n²), Best O(n)        | O(1)                 | Efficient for small or sorted data |
|                           | **Merge Sort**                            | O(n log n)              | O(n)                 | Divide and Conquer                 |
|                           | **Quick Sort**                            | O(n log n), Worst O(n²) | O(log n)             | Partition-based                    |
| **Searching**             | **Linear Search**                         | O(n)                    | O(1)                 | Sequential search                  |
|                           | **Binary Search**                         | O(log n)                | O(1)                 | Sorted array required              |
| **Divide & Conquer**      | **Merge Sort, Quick Sort, Binary Search** | —                       | —                    | Divide into subproblems            |
| **Greedy Algorithms**     | **Activity Selection**                    | O(n log n)              | O(1)                 | Sort by finish time                |
|                           | **Fractional Knapsack**                   | O(n log n)              | O(1)                 | Sort by value/weight ratio         |
|                           | **Huffman Coding**                        | O(n log n)              | O(n)                 | Data compression                   |
|                           | **Dijkstra’s Algorithm**                  | O(V²) or O(E log V)     | O(V)                 | Shortest path (no negatives)       |
|                           | **Prim’s Algorithm**                      | O(V²) or O(E log V)     | O(V)                 | MST (greedy)                       |
|                           | **Kruskal’s Algorithm**                   | O(E log E)              | O(V)                 | MST using Disjoint Set             |
| **Dynamic Programming**   | **0/1 Knapsack**                          | O(nW)                   | O(nW)                | Subset selection                   |
|                           | **Matrix Chain Multiplication**           | O(n³)                   | O(n²)                | Parenthesization                   |
|                           | **Longest Common Subsequence (LCS)**      | O(mn)                   | O(mn)                | Sequence matching                  |
|                           | **Floyd–Warshall**                        | O(V³)                   | O(V²)                | All pairs shortest path            |
|                           | **Bellman–Ford**                          | O(VE)                   | O(V)                 | Handles negative weights           |
| **Graph Algorithms**      | **BFS (Breadth-First Search)**            | O(V+E)                  | O(V)                 | Level-wise traversal               |
|                           | **DFS (Depth-First Search)**              | O(V+E)                  | O(V)                 | Stack / recursion                  |
|                           | **Topological Sort**                      | O(V+E)                  | O(V)                 | DAG ordering                       |
| **Backtracking**          | **N-Queens Problem**                      | O(N!)                   | O(N²)                | Try all placements                 |
|                           | **Sum of Subsets**                        | O(2ⁿ)                   | O(n)                 | Explore all subsets                |
|                           | **Graph Coloring**                        | O(mⁿ)                   | O(n)                 | m = number of colors               |
| **Graph (Shortest Path)** | **Dijkstra’s**                            | O(V²) / O(E log V)      | O(V)                 | No negative edges                  |
|                           | **Bellman–Ford**                          | O(VE)                   | O(V)                 | Works with negative edges          |
|                           | **Floyd–Warshall**                        | O(V³)                   | O(V²)                | All-pairs shortest path            |
|                           | **Multistage Graph**                      | O(E)                    | O(V)                 | Shortest path via stages           |
| **Tree Algorithms**       | **BST Operations**                        | O(log n), Worst O(n)    | O(h)                 | h = tree height                    |
|                           | **AVL Tree**                              | O(log n)                | O(n)                 | Balanced BST                       |
|                           | **Heap Sort**                             | O(n log n)              | O(1)                 | Max heap construction              |
| **Advanced**              | **Union–Find (Disjoint Set)**             | O(α(n))                 | O(n)                 | Used in Kruskal’s                  |
|                           | **TSP (Dynamic Programming)**             | O(n²·2ⁿ)                | O(n·2ⁿ)              | NP-Hard problem                    |
//red black tree
// red_black_tree_insert.cpp
#include <bits/stdc++.h>
using namespace std;

enum Color { RED, BLACK };

struct RBNode {
    int key;
    Color color;
    RBNode *left, *right, *parent;
    RBNode(int k) : key(k), color(RED), left(nullptr), right(nullptr), parent(nullptr) {}
};

class RedBlackTree {
private:
    RBNode *root;
    RBNode *NIL; // sentinel

    void leftRotate(RBNode* x) {
        RBNode* y = x->right;
        x->right = y->left;
        if (y->left != NIL) y->left->parent = x;
        y->parent = x->parent;
        if (x->parent == NIL) root = y;
        else if (x == x->parent->left) x->parent->left = y;
        else x->parent->right = y;
        y->left = x;
        x->parent = y;
    }

    void rightRotate(RBNode* x) {
        RBNode* y = x->left;
        x->left = y->right;
        if (y->right != NIL) y->right->parent = x;
        y->parent = x->parent;
        if (x->parent == NIL) root = y;
        else if (x == x->parent->right) x->parent->right = y;
        else x->parent->left = y;
        y->right = x;
        x->parent = y;
    }

    void fixInsert(RBNode* z) {
        while (z->parent->color == RED) {
            RBNode *gp = z->parent->parent;
            if (z->parent == gp->left) {
                RBNode *y = gp->right; // uncle
                if (y->color == RED) {
                    // Case 1
                    z->parent->color = BLACK;
                    y->color = BLACK;
                    gp->color = RED;
                    z = gp;
                } else {
                    if (z == z->parent->right) {
                        // Case 2
                        z = z->parent;
                        leftRotate(z);
                    }
                    // Case 3
                    z->parent->color = BLACK;
                    gp->color = RED;
                    rightRotate(gp);
                }
            } else {
                RBNode *y = gp->left; // uncle
                if (y->color == RED) {
                    // Case 1
                    z->parent->color = BLACK;
                    y->color = BLACK;
                    gp->color = RED;
                    z = gp;
                } else {
                    if (z == z->parent->left) {
                        // Case 2
                        z = z->parent;
                        rightRotate(z);
                    }
                    // Case 3
                    z->parent->color = BLACK;
                    gp->color = RED;
                    leftRotate(gp);
                }
            }
            if (z == root) break;
        }
        root->color = BLACK;
    }

    void inorderHelper(RBNode* node) {
        if (node != NIL) {
            inorderHelper(node->left);
            cout << node->key << (node->color == RED ? "R " : "B ");
            inorderHelper(node->right);
        }
    }

public:
    RedBlackTree() {
        NIL = new RBNode(0);
        NIL->color = BLACK;
        NIL->left = NIL->right = NIL->parent = NIL;
        root = NIL;
    }

    void insert(int key) {
        RBNode* z = new RBNode(key);
        z->left = z->right = z->parent = NIL;

        RBNode* y = NIL;
        RBNode* x = root;
        while (x != NIL) {
            y = x;
            if (z->key < x->key) x = x->left;
            else x = x->right;
        }
        z->parent = y;
        if (y == NIL) root = z;
        else if (z->key < y->key) y->left = z;
        else y->right = z;

        z->left = z->right = NIL;
        z->color = RED;

        fixInsert(z);
    }

    void inorder() {
        inorderHelper(root);
        cout << endl;
    }

    // Optional: destructor to free nodes (not implemented for brevity)
};

int main() {
    RedBlackTree rbt;
    vector<int> keys = {10, 20, 30, 15, 25, 5, 1, 8};
    for (int k : keys) {
        rbt.insert(k);
        cout << "After inserting " << k << " : ";
        rbt.inorder();
    }
    return 0;
}

//binomial heep

// binomial_heap.cpp
#include <bits/stdc++.h>
using namespace std;

struct BinNode {
    int key;
    int degree;
    BinNode *parent, *child, *sibling;
    BinNode(int k) : key(k), degree(0), parent(nullptr), child(nullptr), sibling(nullptr) {}
};

class BinomialHeap {
private:
    BinNode* head; // head of root list

    BinNode* mergeRootLists(BinNode* h1, BinNode* h2) {
        if (!h1) return h2;
        if (!h2) return h1;
        BinNode *head = nullptr, *tail = nullptr;
        BinNode *a = h1, *b = h2;
        if (a->degree <= b->degree) { head = a; a = a->sibling; }
        else { head = b; b = b->sibling; }
        tail = head;
        while (a && b) {
            if (a->degree <= b->degree) {
                tail->sibling = a; a = a->sibling;
            } else {
                tail->sibling = b; b = b->sibling;
            }
            tail = tail->sibling;
        }
        tail->sibling = (a ? a : b);
        return head;
    }

    void linkTrees(BinNode* y, BinNode* z) {
        // make y a child of z (assuming y.degree == z.degree and y.key >= z.key)
        y->parent = z;
        y->sibling = z->child;
        z->child = y;
        z->degree++;
    }

    BinNode* unionHeaps(BinNode* h1, BinNode* h2) {
        BinNode* newHead = mergeRootLists(h1, h2);
        if (!newHead) return nullptr;

        BinNode *prev = nullptr, *curr = newHead, *next = curr->sibling;
        while (next) {
            if ( (curr->degree != next->degree) ||
                 (next->sibling && next->sibling->degree == curr->degree) ) {
                prev = curr;
                curr = next;
            } else {
                if (curr->key <= next->key) {
                    curr->sibling = next->sibling;
                    linkTrees(next, curr);
                } else {
                    if (prev) prev->sibling = next;
                    else newHead = next;
                    linkTrees(curr, next);
                    curr = next;
                }
            }
            next = curr->sibling;
        }
        return newHead;
    }

public:
    BinomialHeap() : head(nullptr) {}

    void insert(int key) {
        BinNode* node = new BinNode(key);
        BinomialHeap temp;
        temp.head = node;
        head = unionHeaps(head, temp.head);
    }

    BinNode* getMinNode() {
        if (!head) return nullptr;
        BinNode* y = nullptr;
        BinNode* x = head;
        int minKey = INT_MAX;
        while (x) {
            if (x->key < minKey) {
                minKey = x->key;
                y = x;
            }
            x = x->sibling;
        }
        return y;
    }

    int getMin() {
        BinNode* minNode = getMinNode();
        if (!minNode) throw runtime_error("Heap is empty");
        return minNode->key;
    }

    int extractMin() {
        if (!head) throw runtime_error("Heap is empty");
        // find min root and keep track of prev
        BinNode *minPrev = nullptr, *minNode = head;
        BinNode *prev = nullptr, *curr = head;
        int minKey = INT_MAX;
        while (curr) {
            if (curr->key < minKey) { minKey = curr->key; minPrev = prev; minNode = curr; }
            prev = curr; curr = curr->sibling;
        }
        // remove minNode from root list
        if (minPrev) minPrev->sibling = minNode->sibling;
        else head = minNode->sibling;

        // reverse minNode's child list and create new heap
        BinNode* child = minNode->child;
        BinNode* rev = nullptr;
        while (child) {
            BinNode* next = child->sibling;
            child->sibling = rev;
            child->parent = nullptr;
            rev = child;
            child = next;
        }
        // union head with rev (rev is root list of children)
        head = unionHeaps(head, rev);

        int ret = minNode->key;
        delete minNode;
        return ret;
    }

    bool empty() { return head == nullptr; }

    // Utility: print root list (for debugging)
    void printRoots() {
        cout << "Root list: ";
        for (BinNode* x = head; x; x = x->sibling) {
            cout << "(k=" << x->key << ",deg=" << x->degree << ") ";
        }
        cout << endl;
    }
};

int main() {
    cout << "=== Binomial Heap demo ===\n";
    BinomialHeap bh;
    vector<int> vals = {10, 3, 7, 21, 14, 18, 1};
    for (int v : vals) {
        bh.insert(v);
        bh.printRoots();
    }

    cout << "Min = " << bh.getMin() << endl;
    cout << "Extracting all elements in increasing order:\n";
    while (!bh.empty()) {
        cout << bh.extractMin() << " ";
    }
    cout << endl;
    return 0;
}

""")