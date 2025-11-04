def doc():
    print(r"""
mcm() -> MCM (Memoization)
custSort() -> sort any DS from scratch
mergeSort() -> Merge Sort
quickSort() -> Quick Sort
djikstra() -> Dijkstra Algo
prims() -> Prims for MST
kruskal() -> Kruskal for MST
nQueens() -> N-Queens
lcs() -> longest common subsequence
knapsackZeroOne() -> KnapSack Dynamic Programming
custMinHeap() -> Custom Min Heap
jobScheduling() -> Job Scheduling
btmps() -> BinaryTreeMaxPathSum
mr3() -> Meeting Room 3
meft() -> maxEarningFromTaxi
rp()->reversePair
rnikg() -> reverseNodeInKGroups
ksnimt() -> kthSmallestNumberInMultiplicationTable
cnwhs() -> countNodeWithHighestScore

""")
    
def mcm():
    print(r"""
int rec(int i, int j, vector<int> &arr, vector<vector<int>> &dp)
{
    if (i == j)
        return 0;
    if (dp[i][j] != -1)
        return dp[i][j];
    int steps = INT_MAX;
    for (int k = i; k <= j - 1; k++)
    {
        int temp = arr[i - 1] * arr[k] * arr[j] + rec(i, k, arr, dp) + rec(k + 1, j, arr, dp);
        steps = min(temp, steps);
    }
    return dp[i][j] = steps;
}
int matrixMultiplication(vector<int> &arr)
{
    vector<vector<int>> dp(arr.size() + 1, vector<int>(arr.size() + 1, -1));
    return rec(1, arr.size() - 1, arr, dp);
}

""")
    
def custSort():
    print(r"""
#include <iostream>
#include <vector>
using namespace std;

// Comparison function for pairs
bool comparePairs(pair<int, int> a, pair<int, int> b) {
    if (a.first < b.first) return true;
    if (a.first == b.first && a.second < b.second) return true;
    return false;
}

// Merge function
void merge(vector<pair<int, int>>& arr, int left, int mid, int right) {
    int n1 = mid - left + 1;
    int n2 = right - mid;

    vector<pair<int, int>> L(n1);
    vector<pair<int, int>> R(n2);

    for (int i = 0; i < n1; i++)
        L[i] = arr[left + i];
    for (int j = 0; j < n2; j++)
        R[j] = arr[mid + 1 + j];

    int i = 0, j = 0, k = left;

    while (i < n1 && j < n2) {
        if (comparePairs(L[i], R[j])) {
            arr[k] = L[i];
            i++;
        } else {
            arr[k] = R[j];
            j++;
        }
        k++;
    }

    // Copy remaining elements
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

// Recursive merge sort
void mergeSort(vector<pair<int, int>>& arr, int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;

        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);

        merge(arr, left, mid, right);
    }
}

int main() {
    vector<pair<int, int>> v = {
        {3, 5}, {1, 2}, {3, 1}, {2, 8}, {1, 1}
    };

    mergeSort(v, 0, v.size() - 1);

    cout << "Sorted pairs:\n";
    for (auto &p : v)
        cout << "(" << p.first << ", " << p.second << ") ";
    cout << endl;

    return 0;
}
""")

def mergeSort():
    print(r"""
#include <bits/stdc++.h>
using namespace std;

// Merge two sorted halves of arr[l..r]
void mergeArr(vector<int>& arr, int l, int mid, int r) {
    int n1 = mid - l + 1;
    int n2 = r - mid;

    vector<int> left(n1), right(n2);

    for(int i = 0; i < n1; i++)
        left[i] = arr[l + i];
    for(int i = 0; i < n2; i++)
        right[i] = arr[mid + 1 + i];

    int i = 0, j = 0, k = l;

    while(i < n1 && j < n2) {
        if(left[i] <= right[j]) {
            arr[k++] = left[i++];
        }
        else {
            arr[k++] = right[j++];
        }
    }

    while(i < n1) arr[k++] = left[i++];
    while(j < n2) arr[k++] = right[j++];
}

void mergeSort(vector<int>& arr, int l, int r) {
    if(l >= r) return;

    int mid = l + (r - l) / 2;

    mergeSort(arr, l, mid);
    mergeSort(arr, mid + 1, r);

    mergeArr(arr, l, mid, r);
}

int main() {
    vector<int> arr = {5, 3, 8, 4, 2, 7, 1};

    mergeSort(arr, 0, arr.size() - 1);

    for(int x : arr) cout << x << " ";
    return 0;
}

""")
    
def quickSort():
    print(r"""
#include <bits/stdc++.h>
using namespace std;

// Partition function: places pivot in correct sorted position
int partitionArr(vector<int> &arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;

    for(int j = low; j < high; j++) {
        if(arr[j] < pivot) {
            i++;
            swap(arr[i], arr[j]);
        }
    }

    swap(arr[i + 1], arr[high]);
    return i + 1;
}

void quickSort(vector<int> &arr, int low, int high) {
    if(low < high) {
        int pivotIndex = partitionArr(arr, low, high);
        quickSort(arr, low, pivotIndex - 1);
        quickSort(arr, pivotIndex + 1, high);
    }
}

int main() {
    vector<int> arr = {10, 7, 8, 9, 1, 5};
    int n = arr.size();

    quickSort(arr, 0, n - 1);

    cout << "Sorted Array: ";
    for(int num : arr)
        cout << num << " ";
}

""")

def djikstra():
    print(r"""
vector<int> dijkstra(int V, vector<vector<int>> adj[], int S) {
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;

    vector<int> dist(V, 1e9);
    dist[S] = 0;
    pq.push({0, S});

    while(!pq.empty()) {
        int dis = pq.top().first;
        int node = pq.top().second;
        pq.pop();

        for(auto it : adj[node]) {
            int adjNode = it[0];
            int edgeWeight = it[1];

            if(dis + edgeWeight < dist[adjNode]) {
                dist[adjNode] = dis + edgeWeight;
                pq.push({dist[adjNode], adjNode});
            }
        }
    }

    return dist;
}

""")
    
def prims():
    print(r"""
int spanningTree(int V, vector<vector<int>> &edges)
{
    vector<vector<pair<int, int>>> adj(V);

    for (int i = 0; i < edges.size(); i++)
    {
        int u = edges[i][0];
        int v = edges[i][1];
        int wt = edges[i][2];
        adj[u].push_back({wt, v});
        adj[v].push_back({wt, u});
    }

    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    vector<bool> visited(V, false);

    pq.push({0, 0});
    int sum = 0;

    while (!pq.empty())
    {
        auto it = pq.top();
        pq.pop();

        int node = it.second;
        int weight = it.first;

        if (visited[node])
            continue;

        visited[node] = true;
        sum += weight;

        for (auto adjPair : adj[node])
        {
            int adjWt = adjPair.first;
            int adjNode = adjPair.second;

            if (!visited[adjNode])
            {
                pq.push({adjWt, adjNode});
            }
        }
    }
    return sum;
}
""")
    
def kruskal():
    print(r"""

""")
    
def nQueens():
    print(r"""
class Solution {
public:
bool isValid(int row, int col, vector<string>board,vector<bool>&isRowTaken,vector<bool>&lowerDiagonal,vector<bool>&upperDiagonal){
    int n = board.size();
    if(isRowTaken[row]) return false;

    if(lowerDiagonal[row+col]) return false;

    if(upperDiagonal[n-1 + col - row]) return false;
    
    return true;
}
void rec(int col,int n,vector<string>&board,vector<vector<string>>&ans,vector<bool>&isRowTaken,vector<bool>&lowerDiagonal,vector<bool>&upperDiagonal){
    if(col==n){
        ans.push_back(board);
        return;
    }
    for(int i = 0;i<n;i++){
        if(isValid(i,col,board,isRowTaken,lowerDiagonal,upperDiagonal)){
            board[i][col] = 'Q';
            isRowTaken[i] = true;
            lowerDiagonal[i+col] = true;
            upperDiagonal[n-1+col-i] = true;
            rec(col+1,n,board,ans,isRowTaken,lowerDiagonal,upperDiagonal);
            board[i][col] = '.';
            isRowTaken[i] = false;
            lowerDiagonal[i+col] = false;
            upperDiagonal[n-1+col-i] = false;
        }
    }
}
    vector<vector<string>> solveNQueens(int n) {
        vector<bool>isRowTaken(n,false);
        vector<bool>lowerDiagonal(2*n-1,false);
        vector<bool>upperDiagonal(2*n-1,false);
        vector<string>board(n);
        vector<vector<string>>ans;
        for(int i = 0;i<n;i++){
            for(int j = 0;j<n;j++){
                board[i].push_back('.');
            }
        }
        rec(0,n,board,ans,isRowTaken,lowerDiagonal,upperDiagonal);
        return ans;
    }
};
""")
    
def lcs():
    print(r"""
#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    int rec(int i, int j, string &s1, string &s2, vector<vector<int>>& dp) {
        // If any string ends, LCS is zero from here
        if(i == s1.size() || j == s2.size())
            return 0;
        
        // If already computed
        if(dp[i][j] != -1)
            return dp[i][j];
        
        // If characters match, take 1 + LCS of rest
        if(s1[i] == s2[j])
            return dp[i][j] = 1 + rec(i + 1, j + 1, s1, s2, dp);
        
        // Else we either ignore a char from s1 or s2
        int takeS1 = rec(i + 1, j, s1, s2, dp);
        int takeS2 = rec(i, j + 1, s1, s2, dp);
        
        return dp[i][j] = max(takeS1, takeS2);
    }

    int longestCommonSubsequence(string s1, string s2) {
        int n = s1.size(), m = s2.size();
        vector<vector<int>> dp(n, vector<int>(m, -1));
        return rec(0, 0, s1, s2, dp);
    }
};

""")
    
def knapsackZeroOne():
    print(r"""
#include <vector>
#include <algorithm>
using namespace std;

class solution {
private:
    int robhelper(vector<int>& nums, int i, vector<int>& memo) {
        if (i < 0)
            return 0;
        if (memo[i] != -1)
            return memo[i];

        int take = nums[i] + robhelper(nums, i - 2, memo);
        int not_take = robhelper(nums, i - 1, memo);

        memo[i] = max(take, not_take);
        return memo[i];
    }

public:
    int rob(vector<int>& nums) {
        vector<int> memo(nums.size(), -1);
        return robhelper(nums, nums.size() - 1, memo);
    }
};
""")
    
def custMinHeap():
    print(r"""
#include <iostream>
#include <vector>
using namespace std;

class MinHeap {
    vector<int> heap;

    // Maintain heap property after insertion (bottom-up)
    void heapifyUp(int index) {
        int parent = (index - 1) / 2;
        while (index > 0 && heap[index] < heap[parent]) {
            swap(heap[index], heap[parent]);
            index = parent;
            parent = (index - 1) / 2;
        }
    }

    // Maintain heap property after deletion (top-down)
    void heapifyDown(int index) {
        int size = heap.size();
        int left = 2 * index + 1;
        int right = 2 * index + 2;
        int smallest = index;

        if (left < size && heap[left] < heap[smallest])
            smallest = left;

        if (right < size && heap[right] < heap[smallest])
            smallest = right;

        if (smallest != index) {
            swap(heap[index], heap[smallest]);
            heapifyDown(smallest);
        }
    }

public:
    // Insert element
    void push(int val) {
        heap.push_back(val);
        heapifyUp(heap.size() - 1);
    }

    // Remove smallest element
    void pop() {
        if (heap.empty()) return;
        heap[0] = heap.back();
        heap.pop_back();
        heapifyDown(0);
    }

    // Get smallest element
    int top() {
        if (heap.empty()) return -1;
        return heap[0];
    }

    bool empty() {
        return heap.empty();
    }

    int size() {
        return heap.size();
    }

    // Print heap (for debugging)
    void print() {
        for (int x : heap) cout << x << " ";
        cout << endl;
    }
};

int main() {
    MinHeap h;
    h.push(10);
    h.push(5);
    h.push(20);
    h.push(3);

    cout << "Heap elements: ";
    h.print();  // not sorted, but heap property holds

    cout << "Min element: " << h.top() << endl;  // 3

    h.pop();
    cout << "After popping, new min: " << h.top() << endl;  // 5
}
""")
    
def jobScheduling():
    print(r"""
#include<bits/stdc++.h>

using namespace std;
// A structure to represent a job 
struct Job {
   int id; // Job Id 
   int dead; // Deadline of job 
   int profit; // Profit if job is over before or on deadline 
};
class Solution {
   public:
      bool static comparison(Job a, Job b) {
         return (a.profit > b.profit);
      }
   //Function to find the maximum profit and the number of jobs done
   pair < int, int > JobScheduling(Job arr[], int n) {

      sort(arr, arr + n, comparison);
      int maxi = arr[0].dead;
      for (int i = 1; i < n; i++) {
         maxi = max(maxi, arr[i].dead);
      }

      int slot[maxi + 1];

      for (int i = 0; i <= maxi; i++)
         slot[i] = -1;

      int countJobs = 0, jobProfit = 0;

      for (int i = 0; i < n; i++) {
         for (int j = arr[i].dead; j > 0; j--) {
            if (slot[j] == -1) {
               slot[j] = i;
               countJobs++;
               jobProfit += arr[i].profit;
               break;
            }
         }
      }

      return make_pair(countJobs, jobProfit);
   }
};
int main() {
   int n = 4;
   Job arr[n] = {{1,4,20},{2,1,10},{3,2,40},{4,2,30}};

   Solution ob;
   //function call
   pair < int, int > ans = ob.JobScheduling(arr, n);
   cout << ans.first << " " << ans.second << endl;

   return 0;
}
""")
    
def btmps():
    print(r"""
#include <bits/stdc++.h>
using namespace std;

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode(int x) : val(x), left(NULL), right(NULL) {}
};

class Solution {
public:
    int maxSum;

    int dfs(TreeNode* root) {
        if(!root) return 0;

        int left = max(0, dfs(root->left));   // ignore negative
        int right = max(0, dfs(root->right));

        // best path with root as highest node
        maxSum = max(maxSum, root->val + left + right);

        // return best single-way path to parent
        return root->val + max(left, right);
    }

    int maxPathSum(TreeNode* root) {
        maxSum = INT_MIN;
        dfs(root);
        return maxSum;
    }
};

""")
    
def mr3():
    print(r"""
class Solution {
public:
    int mostBooked(int n, vector<vector<int>>& meetings) {
        vector<long long> busy(n, 0); 
        vector<int> count(n, 0);      

        sort(meetings.begin(), meetings.end());

        for (auto& meeting : meetings) {
            int start = meeting[0], end = meeting[1];
            long long earliest = LLONG_MAX;
            int roomIndex = -1;
            bool assigned = false;

            for (int i = 0; i < n; ++i) {
                if (busy[i] < earliest) {
                    earliest = busy[i];
                    roomIndex = i;
                }
                if (busy[i] <= start) {
                    busy[i] = end;
                    count[i]++;
                    assigned = true;
                    break;
                }
            }

            if (!assigned) {
                busy[roomIndex] += (end - start);
                count[roomIndex]++;
            }
        }

        int res = 0, maxCount = 0;
        for (int i = 0; i < n; ++i) {
            if (count[i] > maxCount) {
                maxCount = count[i];
                res = i;
            }
        }
        return res;
    }
};
""")
    
def meft():
    print(r"""
#define pii pair<int, int>
class Solution {
public:
    long long maxTaxiEarnings(int n, vector<vector<int>>& rides) {
        vector<vector<pii>> rideStartAt(n);
        for (auto& ride : rides) {
            int s = ride[0], e = ride[1], t = ride[2];
            rideStartAt[s].push_back({e, e - s + t});  
        }
        vector<long long> dp(n+1);
        for (int i = n-1; i >= 1; --i) {
            for (auto& [e, d] : rideStartAt[i]) {
                dp[i] = max(dp[i], dp[e] + d);
            }
            dp[i] = max(dp[i], dp[i + 1]);
        }
        return dp[1];
    }
};
""")
    
def rp():
    print(r"""
class Solution {
public:
    void merge(vector<int>& arr, int low, int mid, int high) {
        vector<int> temp;
        int left = low;
        int right = mid + 1;
        while (left <= mid && right <= high) {
            if (arr[left] <= arr[right]) {
                temp.push_back(arr[left]);
                left++;
            } else {
                temp.push_back(arr[right]);
                right++;
            }
        }
        while (left <= mid) {
            temp.push_back(arr[left]);
            left++;
        }
        while (right <= high) {
            temp.push_back(arr[right]);
            right++;
        }
        for (int i = low; i <= high; i++) {
            arr[i] = temp[i - low];
        }
    }
    int countPairs(vector<int>& arr, int low, int mid, int high) {
    int right = mid + 1;
    int cnt = 0;
    for (int i = low; i <= mid; i++) {
        while (right <= high && (long long)arr[i] > 2LL * arr[right])
            right++;
        cnt += (right - (mid + 1));
    }
    return cnt;
}


    int mergeSort(vector<int>& arr, int low, int high) {
        int cnt = 0;
        if (low >= high)
            return cnt;
        int mid = (low + high) / 2;
        cnt += mergeSort(arr, low, mid);        
        cnt += mergeSort(arr, mid + 1, high);   
        cnt += countPairs(arr, low, mid, high); 
        merge(arr, low, mid, high);             
        return cnt;
    }

    int reversePairs(vector<int>& nums) {
        return mergeSort(nums, 0, nums.size() - 1);
    }
};
""")
    
def rnikg():
    print(r"""
class Solution {
public:
    ListNode* reverseLL(ListNode* head) {
        ListNode* prev = nullptr;
        ListNode* curr = head;
        while (curr) {
            ListNode* nextNode = curr->next;
            curr->next = prev;
            prev = curr;
            curr = nextNode;
        }
        return prev;
    }

    ListNode* findKthListNode(ListNode* temp, int k) {
        while (temp && k > 1) {
            temp = temp->next;
            k--;
        }
        return temp;
    }

    ListNode* reverseKGroup(ListNode* head, int k) {
        if (!head || k == 1) return head;

        ListNode* temp = head;
        ListNode* prevNode = nullptr;

        while (temp) {
            ListNode* kthListNode = findKthListNode(temp, k);
            if (!kthListNode) {
                if (prevNode) prevNode->next = temp;
                break;
            }

            ListNode* nextNode = kthListNode->next;
            kthListNode->next = nullptr; 

            ListNode* newHead = reverseLL(temp); 

            if (head == temp) {
                head = newHead; 
            } else {
                prevNode->next = newHead; 
            }

            prevNode = temp;  
            temp = nextNode;  
        }
        return head;
    }
};

""")
    
def ksnimt():
    print(r"""
class Solution {
public:
    int count(int m, int n, int x) {
        int ans = 0;
        for (int i = 1; i <= m; i++)
            ans += min(x / i, n);
        return ans;
    }
    int findKthNumber(int m, int n, int k) {
        int low = 1, high = m * n, mid, ans;
        while (low <= high) {
            mid = (low + high) >> 1;
            if (count(m, n, mid) < k)
                low = mid + 1;
            else {
                high = mid - 1;
                ans = mid;
            }
        }
        return ans;
    }
};
""")