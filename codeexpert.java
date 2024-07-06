import java.lang.Math;

import java.util.*;

class Main {

    public static void main(String[] args) {

        // Uncomment this line if you want to read from a file

        In.open("public/sample.in");

        Out.compareTo("public/sample.out");

        int t = In.readInt();

        for (int i = 0; i < t; i++) {

            testCase();

        }

        // Uncomment this line if you want to read from a file

        In.close();

    }

    public static void testCase() {

        // Input using In.java class

        int n = In.readInt();

        int k = In.readInt();

        int m = In.readInt();

        double[] p = new double[n];

        double[][] DP = new double[n][m];

        for (int i = 0; i < n; i++) {

            for (int j = 0; j < m; j++) {

                DP[i][j] = -1.0;

            }

        }

        for (int i = 0; i < n; i++) {

            p[i] = In.readDouble();

        }

        Out.println(compute(0, k, n, m, p, DP));

        // Output using Out.java class

    }

    public static double compute(int day, double wealth, int n, int m, double[] p, double[][] DP) {
        if (wealth >= m)
            return 1;
        if (day == n) {
            if (wealth >= m) {
                // System.out.println(prob);
                return 1;
            }
            return 0;
        }

        if (DP[day][(int) wealth] != -1)
            return DP[day][(int) wealth];

        double res = compute(day + 1, wealth, n, m, p, DP);

        for (int b = 1; b <= wealth; b++) {
            res = Math.max(res, p[day] * compute(day + 1, wealth + b, n, m, p, DP)
                    + (1 - p[day]) * compute(day + 1, wealth - b, n, m, p, DP));
        }

        DP[day][(int) wealth] = res;
        return res;

    }

}