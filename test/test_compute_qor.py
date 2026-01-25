from common.objectives.compute_qor import compute_qor

def main():
    ref_metrics = {
        "lut": 100,
        "level": 20,
    }

    # Case 1: ref so với chính nó → QoR = 1 + 1 = 2
    qor_ref = compute_qor(ref_metrics, ref_metrics)
    print("QoR(ref vs ref) =", qor_ref)

    # Case 2: test thêm cho chắc
    test_metrics = {
        "lut": 120,
        "level": 18,
    }
    qor_test = compute_qor(test_metrics, ref_metrics)
    print("QoR(test vs ref) =", qor_test)


if __name__ == "__main__":
    main()

