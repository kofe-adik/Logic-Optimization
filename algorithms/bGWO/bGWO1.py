import numpy as np
from typing import Tuple
from algorithms.bGWO.utils import evaluate_design, fitness


class BinaryGWO:
    def __init__(
        self,
        pop_size: int,
        dim: int,
        iters: int,
        design: str,
        lut_k: int,
        seed: int | None = None,
    ):
        assert dim % 4 == 0, "dim must be multiple of 4"

        # ---------------- CONFIG ----------------
        self.pop_size = pop_size
        self.dim = dim
        self.iters = iters
        self.design = design
        self.lut_k = lut_k

        # RNG
        self.rng = np.random.default_rng(seed)

        # ---------------- BASELINE ----------------
        baseline_bits = np.array(
            [0,1,1,0, 0,0,0,0, 0,0,1,0, 0,1,1,0, 0,0,0,0,
             0,0,0,1, 0,1,1,0, 0,0,1,1, 0,0,0,1, 0,1,1,0],
            dtype=np.uint8
        )

        self.ref_lut, self.ref_level = evaluate_design(
            design_file=self.design,
            bits=baseline_bits.tolist(),
            lut_k=self.lut_k,
        )

        # ---------------- POPULATION ----------------
        self.pop = self.rng.integers(0, 2, size=(pop_size, dim), dtype=np.uint8)

        # ---------------- FITNESS ----------------
        self.pop_f = np.full(pop_size, np.inf)

        # ---------------- LEADERS ----------------
        self.x_alpha = None
        self.x_beta = None
        self.x_delta = None
        self.x_alpha_f = np.inf
        self.x_beta_f = np.inf
        self.x_delta_f = np.inf

        # ---------------- INIT GWO COEFF ----------------
        self.update_coeff(None)

        # ---------------- INIT EVAL ----------------
        self.evaluate_population()
        self.update_leaders()

        print("[BinaryGWO] INIT DONE")
        print("REF: LUT = ", self.ref_lut, " - LEVEL = ", self.ref_level)
        print(f"pop shape: {self.pop.shape}")
        print(f"pop fitness: {self.pop_f}")
        print("A shape: alpha = ", self.A_alpha.shape, " beta = ", self.A_beta.shape, " delta = ", self.A_delta.shape)
        print("C shape: alpha = ", self.C_alpha.shape, " beta = ", self.C_beta.shape, " delta = ", self.C_delta.shape)
        print("ALPHA: ", self.x_alpha, " - Fitness: ", self.x_alpha_f)
        print("BETA:  ", self.x_beta, " - Fitness: ", self.x_beta_f)
        print("DELTA: ", self.x_delta, " - Fitness: ", self.x_delta_f)


    # -----------------------------------------
    def update_coeff(self, t: int | None):
        # a decreases linearly from 2 → 0
        if t is None:
            self.a = 2.0
        else:
            self.a = 2.0 - 2.0 * t / self.iters

        # r1, r2 tensors
        self.r1_alpha = self.rng.random((self.pop_size, self.dim))
        self.r1_beta  = self.rng.random((self.pop_size, self.dim))
        self.r1_delta = self.rng.random((self.pop_size, self.dim))

        self.r2_alpha = self.rng.random((self.pop_size, self.dim))
        self.r2_beta  = self.rng.random((self.pop_size, self.dim))
        self.r2_delta = self.rng.random((self.pop_size, self.dim))

        # A tensors
        self.A_alpha = 2 * self.a * self.r1_alpha - self.a
        self.A_beta  = 2 * self.a * self.r1_beta  - self.a
        self.A_delta = 2 * self.a * self.r1_delta - self.a

        # C tensors
        self.C_alpha = 2 * self.r2_alpha
        self.C_beta  = 2 * self.r2_beta
        self.C_delta = 2 * self.r2_delta

    # ------------------------------------------
    def evaluate_population(self):
        for i in range(self.pop_size):
            bits = self.pop[i].tolist()

            lut, level = evaluate_design(
                design_file=self.design,
                bits=bits,
                lut_k=self.lut_k,
            )

            qor, _ = fitness(self.ref_lut, self.ref_level, lut, level)
            self.pop_f[i] = qor

        #print("[GWO] Population evaluated")

    # ------------------------------------------
    def update_leaders(self):
        idx = np.argsort(self.pop_f)
        i1, i2, i3 = idx[:3]

        # first init
        if self.x_alpha is None:
            self.x_alpha = self.pop[i1].copy()
            self.x_beta = self.pop[i2].copy()
            self.x_delta = self.pop[i3].copy()

            self.x_alpha_f = self.pop_f[i1]
            self.x_beta_f = self.pop_f[i2]
            self.x_delta_f = self.pop_f[i3]
            return

        # merge old + new
        pool_bits = np.vstack([self.x_alpha, self.x_beta, self.x_delta, self.pop[i1], self.pop[i2], self.pop[i3]])
        pool_fit  = np.array([self.x_alpha_f, self.x_beta_f, self.x_delta_f,
                              self.pop_f[i1], self.pop_f[i2], self.pop_f[i3]])

        order = np.argsort(pool_fit)

        self.x_alpha = pool_bits[order[0]].copy()
        self.x_beta = pool_bits[order[1]].copy()
        self.x_delta = pool_bits[order[2]].copy()
        self.x_alpha_f, self.x_beta_f, self.x_delta_f = pool_fit[order[:3]].tolist()

    # -----------------------------------------
    def compute_D(self):
        """
        Compute distance tensors D_alpha, D_beta, D_delta
        Shape: (pop_size, dim)
        """

        # broadcast leader (dim,) → (pop_size, dim)
        X1 = self.x_alpha  # alpha
        X2 = self.x_beta  # beta
        X3 = self.x_delta  # delta

        # Continuous GWO canonical distance
        self.D_alpha = np.abs(self.C_alpha * X1 - self.pop)
        self.D_beta  = np.abs(self.C_beta  * X2 - self.pop)
        self.D_delta = np.abs(self.C_delta * X3 - self.pop)

    # ------------------------------------------
    def compute_cstep(self):
        self.cstep_alpha = 1.0 / (1.0 + np.exp(-10.0 * (self.A_alpha * self.D_alpha - 0.5)))
        self.cstep_beta  = 1.0 / (1.0 + np.exp(-10.0 * (self.A_beta  * self.D_beta  - 0.5)))
        self.cstep_delta = 1.0 / (1.0 + np.exp(-10.0 * (self.A_delta * self.D_delta - 0.5)))

    # ------------------------------------------
    def compute_bstep(self):
        rand_alpha = self.rng.random((self.pop_size, self.dim))
        rand_beta  = self.rng.random((self.pop_size, self.dim))
        rand_delta = self.rng.random((self.pop_size, self.dim))

        self.bstep_alpha = (self.cstep_alpha >= rand_alpha).astype(np.uint8)
        self.bstep_beta  = (self.cstep_beta  >= rand_beta ).astype(np.uint8)
        self.bstep_delta = (self.cstep_delta >= rand_delta).astype(np.uint8)

    # ------------------------------------------
    def compute_x(self):
        Xa = self.x_alpha[None, :]
        Xb = self.x_beta[None, :]
        Xd = self.x_delta[None, :]

        self.X1 = ((Xa + self.bstep_alpha) >= 1).astype(np.uint8)
        self.X2 = ((Xb + self.bstep_beta ) >= 1).astype(np.uint8)
        self.X3 = ((Xd + self.bstep_delta) >= 1).astype(np.uint8)

    # -------------------------------------------
    def crossover(self):
        """
        Discrete 3-parent crossover:
        xd = X1 if rand < 1/3
             X2 if 1/3 <= rand < 2/3
             X3 otherwise
        """

        r = self.rng.random((self.pop_size, self.dim))

        self.pop = np.where(
            r < 1/3, self.X1,
            np.where(r < 2/3, self.X2, self.X3)
        ).astype(np.uint8)


    # -------------------------------------------
    def run(self):
        """
        Main Binary GWO optimization loop.
       Returns:
            best_bits, best_fitness
        """

        for t in range(self.iters):
            # ---------------- STEP I: update coefficients a, A, C
            # self.update_coeff(t)

            # ---------------- STEP II: compute D, cstep, bstep, X1,X2,X3
            self.compute_D()
            self.compute_cstep()
            self.compute_bstep()
            self.compute_x()

            # ---------------- STEP III: crossover to update population
            self.crossover()

            # ---------------- STEP IV: evaluate new population
            self.update_coeff(t+1)
            self.evaluate_population()

            # ---------------- STEP V: update leaders α β δ
            self.update_leaders()

            # Optional logging
            print(f"[Iter {t + 1:03d}] best = {self.x_alpha_f}")
            print("ALPHA: ", self.x_alpha)
            print("BETA:  ", self.x_beta)
            print("DELTA: ", self.x_delta)

        return self.x_alpha.copy(), self.x_alpha_f

    # -------------------------------------------
    def test(self):
        pass


if __name__ == "__main__":
    gwo = BinaryGWO(
        pop_size=100,
        dim=80,
        iters=200,
        design="./benchmarks/epfl/arithmetic/adder.blif",
        lut_k=6,
        seed=42,
    )
    res_seq, res_qor = gwo.run() 
