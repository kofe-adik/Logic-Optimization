import os
import argparse
import numpy as np
import logging
from concurrent.futures import ProcessPoolExecutor
from algorithms.bGWO.utils import evaluate_design, fitness


# =========================================================
# Worker
# =========================================================
def evaluate_individual(args):
    design, lut_k, ref_lut, ref_level, bits = args

    lut, level = evaluate_design(
        design_file=design,
        bits=bits,
        lut_k=lut_k,
    )

    qor, improve = fitness(
        ref_lut,
        ref_level,
        lut,
        level,
    )

    return qor, improve


# =========================================================
# Binary GWO
# =========================================================
class BinaryGWO:
    def __init__(
        self,
        pop_size: int,
        dim: int,
        iters: int,
        design_name: str,
        lut_k: int,
        seed: int,
        n_workers: int | None = None,
    ):
        assert dim % 4 == 0, "dim must be multiple of 4"

        self.pop_size = pop_size
        self.dim = dim
        self.iters = iters
        self.design_name = design_name
        self.lut_k = lut_k
        self.seed = seed
        self.n_workers = n_workers

        # -------------------------------------------------
        # Auto build design path
        # -------------------------------------------------
        self.design = f"./benchmarks/epfl/arithmetic/{design_name}.blif"

        if not os.path.exists(self.design):
            raise FileNotFoundError(f"Design not found: {self.design}")

        # -------------------------------------------------
        # Auto build logdir
        # -------------------------------------------------
        option = f"lut_k_{lut_k}-pop_{pop_size}-dim_{dim}-iters_{iters}"

        self.logdir = os.path.join(
            "./results/runs/bGWO1",
            option,
            design_name,
            str(seed),
        )

        os.makedirs(self.logdir, exist_ok=True)

        logfile = os.path.join(self.logdir, "run.log")

        # -------------------------------------------------
        # RNG
        # -------------------------------------------------
        self.rng = np.random.default_rng(seed)

        # -------------------------------------------------
        # Logging
        # -------------------------------------------------
        self.logger = logging.getLogger(f"BinaryGWO_{seed}")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        self.logger.propagate = False

        formatter = logging.Formatter(
            "[%(asctime)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        # console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # file
        fh = logging.FileHandler(logfile, mode="w")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # -------------------------------------------------
        # BASELINE
        # -------------------------------------------------
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

        # -------------------------------------------------
        # POPULATION
        # -------------------------------------------------
        self.pop = self.rng.integers(0, 2, size=(pop_size, dim), dtype=np.uint8)
        self.pop_f = np.full(pop_size, np.inf)
        self.pop_improve = np.zeros(pop_size)

        # LEADERS
        self.x_alpha = None
        self.x_alpha_f = np.inf
        self.x_alpha_improve = 0.0

        self.update_coeff(None)
        self.evaluate_population()
        self.update_leaders()

        self.logger.info(
            f"DESIGN={design_name} "
            f"LUT_K={lut_k} POP={pop_size} DIM={dim} ITERS={iters} SEED={seed}"
        )
        self.logger.info(
            f"REF LUT={self.ref_lut} LEVEL={self.ref_level}"
        )

    # -----------------------------------------------------
    def update_coeff(self, t: int | None):
        if t is None:
            self.a = 2.0
        else:
            self.a = 2.0 - 2.0 * t / self.iters
            #self.a = 2.0 - 2.0 * ((np.exp(t / self.iters) - 1.0) / (np.e - 1.0))

        self.r1_alpha = self.rng.random((self.pop_size, self.dim))
        self.r1_beta  = self.rng.random((self.pop_size, self.dim))
        self.r1_delta = self.rng.random((self.pop_size, self.dim))

        self.r2_alpha = self.rng.random((self.pop_size, self.dim))
        self.r2_beta  = self.rng.random((self.pop_size, self.dim))
        self.r2_delta = self.rng.random((self.pop_size, self.dim))

        self.A_alpha = 2 * self.a * self.r1_alpha - self.a
        self.A_beta  = 2 * self.a * self.r1_beta  - self.a
        self.A_delta = 2 * self.a * self.r1_delta - self.a

        self.C_alpha = 2 * self.r2_alpha
        self.C_beta  = 2 * self.r2_beta
        self.C_delta = 2 * self.r2_delta

    # -----------------------------------------------------
    def evaluate_population(self):

        # Nếu population nhỏ thì không cần spawn process
        if self.pop_size < 4 or self.n_workers == 1:
            for i in range(self.pop_size):
                bits = self.pop[i].tolist()
                lut, level = evaluate_design(
                    design_file=self.design,
                    bits=bits,
                    lut_k=self.lut_k,
                )
                qor, improve = fitness(
                    self.ref_lut,
                    self.ref_level,
                    lut,
                    level,
                )
                self.pop_f[i] = qor
                self.pop_improve[i] = improve
            return

        # Parallel
        args = [
            (
                self.design,
                self.lut_k,
                self.ref_lut,
                self.ref_level,
                self.pop[i].tolist(),
            )
            for i in range(self.pop_size)
        ]

        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            results = list(executor.map(evaluate_individual, args))

        for i, (qor, improve) in enumerate(results):
            self.pop_f[i] = qor
            self.pop_improve[i] = improve

    # -----------------------------------------------------
    def update_leaders(self):
        idx = np.argsort(self.pop_f)
        i1, i2, i3 = idx[:3]

        if self.x_alpha is None:
            self.x_alpha = self.pop[i1].copy()
            self.x_beta = self.pop[i2].copy()
            self.x_delta = self.pop[i3].copy()

            self.x_alpha_f = self.pop_f[i1]
            self.x_beta_f = self.pop_f[i2]
            self.x_delta_f = self.pop_f[i3]

            self.x_alpha_improve = self.pop_improve[i1]
            self.x_beta_improve = self.pop_improve[i2]
            self.x_delta_improve = self.pop_improve[i3]
            return

        pool_bits = np.vstack([
            self.x_alpha,
            self.x_beta,
            self.x_delta,
            self.pop[i1],
            self.pop[i2],
            self.pop[i3],
        ])

        pool_fit = np.array([
            self.x_alpha_f,
            self.x_beta_f,
            self.x_delta_f,
            self.pop_f[i1],
            self.pop_f[i2],
            self.pop_f[i3],
        ])

        pool_improve = np.array([
            self.x_alpha_improve,
            self.x_beta_improve,
            self.x_delta_improve,
            self.pop_improve[i1],
            self.pop_improve[i2],
            self.pop_improve[i3],
        ])

        order = np.argsort(pool_fit)

        self.x_alpha = pool_bits[order[0]].copy()
        self.x_alpha_f = pool_fit[order[0]]
        self.x_alpha_improve = pool_improve[order[0]]

        self.x_beta = pool_bits[order[1]].copy()
        self.x_beta_f = pool_fit[order[1]]
        self.x_beta_improve = pool_improve[order[1]]

        self.x_delta = pool_bits[order[2]].copy()
        self.x_delta_f = pool_fit[order[2]]
        self.x_delta_improve = pool_improve[order[2]]

    # -------------------------------------------
    def compute_D(self):
        self.D_alpha = np.abs(self.C_alpha * self.x_alpha - self.pop)
        self.D_beta  = np.abs(self.C_beta  * self.x_beta  - self.pop)
        self.D_delta = np.abs(self.C_delta * self.x_delta - self.pop)


    def compute_x(self):

        Xa = self.x_alpha[None, :]
        Xb = self.x_beta[None, :]
        Xd = self.x_delta[None, :]

        # GWO continuous update
        self.X1 = Xa - self.A_alpha * self.D_alpha
        self.X2 = Xb - self.A_beta  * self.D_beta
        self.X3 = Xd - self.A_delta * self.D_delta

        # ---- GWO mean position ----
        X_mean = (self.X1 + self.X2 + self.X3) / 3.0

        # ---- Adaptive sigmoid slope (2 → 18 theo a) ----
        #k = 5 
        k = 5  + (2 - self.a) * 5

        # ---- S-shape transfer ----
        S = 1.0 / (1.0 + np.exp(-k * (X_mean - 0.5)))

        # ---- Binary update x(t+1) ----
        r = self.rng.random(self.pop.shape)
        self.pop = (r < S).astype(np.uint8)

    # -----------------------------------------------------
    def run(self):
        for t in range(self.iters):

            self.compute_D()
#            self.compute_cstep()            
#            self.compute_bstep()
            self.compute_x()

#            self.crossover()

            self.update_coeff(t + 1)
            self.evaluate_population()
            self.update_leaders()

            self.logger.info(
                f"[Iter {t+1:03d}] "
                f"a={self.a:.2f} | "
                f"qor={self.x_alpha_f:.6f} | "
                f"improve={self.x_alpha_improve:.4f}% | "
                f"alpha={''.join(self.x_alpha.astype(str))}"
            )

        return self.x_alpha.copy(), self.x_alpha_f


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--design", type=str, required=True,
                        help="adder | bar | hyp | ...")

    parser.add_argument("--pop", type=int, default=100)
    parser.add_argument("--dim", type=int, default=80)
    parser.add_argument("--iters", type=int, default=200)
    parser.add_argument("--lut_k", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=None)

    args = parser.parse_args()

    gwo = BinaryGWO(
        pop_size=args.pop,
        dim=args.dim,
        iters=args.iters,
        design_name=args.design,
        lut_k=args.lut_k,
        seed=args.seed,
        n_workers=args.workers,
    )

    res_seq, res_qor = gwo.run()
