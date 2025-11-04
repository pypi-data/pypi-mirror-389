"""Command-line interface for vcf2bedgraph."""

import argparse
import sys
from pathlib import Path

import pysam
from cyvcf2 import VCF


def main() -> None:
    """Main entry point for the vcf2bedgraph CLI."""
    parser = argparse.ArgumentParser(
        description="Convert VCF files to BedGraph format with variant allele frequencies"
    )
    parser.add_argument(
        "vcf",
        type=str,
        help="Path to the input VCF file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Path to the output BedGraph file",
    )
    parser.add_argument(
        "--filter-gq",
        type=int,
        default=0,
        help="Minimum genotype quality threshold (default: 0)",
    )
    parser.add_argument(
        "--filter-dp",
        type=int,
        default=10,
        help="Minimum depth threshold (default: 10)",
    )
    parser.add_argument(
        "--filter-qual",
        type=int,
        default=20,
        help="Minimum variant quality threshold (default: 20)",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Skip compression and indexing of the output BedGraph file",
    )

    args = parser.parse_args()

    # Validate input file exists
    vcf_path = Path(args.vcf)
    if not vcf_path.exists():
        print(f"Error: VCF file not found: {args.vcf}", file=sys.stderr)
        sys.exit(1)

    try:
        # Open VCF file
        vcf = VCF(str(vcf_path))

        # Open output file for writing
        with open(args.output, "w") as out_f:
            # Write BedGraph header
            # out_f.write("track name=vcf2bedgraph description=VCF_to_BedGraph\n")

            # Stream through VCF
            for variant in vcf:
                # Check if FILTER is PASS (empty string means PASS in cyvcf2)
                if variant.FILTER and variant.FILTER != "PASS":
                    continue

                # Check QUAL (variant quality)
                if variant.QUAL < args.filter_qual:
                    continue

                # Get genotype quality (GQ)
                try:
                    gq_values = variant.format("GQ")
                    if gq_values is None or len(gq_values) == 0:
                        continue
                    gq = gq_values[0][0]
                    if gq < args.filter_gq:
                        continue
                except Exception:
                    continue

                # Check depth (DP)
                try:
                    dp_values = variant.format("DP")
                    if dp_values is None or len(dp_values) == 0:
                        continue
                    dp = dp_values[0][0]
                    if dp < args.filter_dp:
                        continue
                except Exception:
                    continue

                # Get VAF from the first sample
                try:
                    vaf_values = variant.format("VAF")
                    if vaf_values is None or len(vaf_values) == 0:
                        continue
                    vaf = vaf_values[0][0]
                except Exception:
                    continue

                # Write BedGraph line
                # Format: chrom start end value
                # VCF is 1-based, BedGraph is 0-based for start
                chrom = variant.CHROM
                start = variant.POS - 1
                end = variant.POS
                out_f.write(f"{chrom}\t{start}\t{end}\t{vaf:.4f}\n")

    except Exception as e:
        print(f"Error processing VCF: {e}", file=sys.stderr)
        sys.exit(1)

    # Compress and index by default (unless --no-compress is specified)
    if not args.no_compress:
        try:
            output_path = Path(args.output)
            compressed_path = Path(f"{args.output}.gz")

            print(f"Compressing {output_path} to {compressed_path}...", file=sys.stderr)
            pysam.tabix_compress(
                str(output_path),
                str(compressed_path),
                force=True,
            )

            print(f"Indexing {compressed_path}...", file=sys.stderr)
            pysam.tabix_index(
                str(compressed_path),
                preset="bed",
                force=True,
            )

            print(
                f"Successfully created {compressed_path} and {compressed_path}.tbi",
                file=sys.stderr,
            )

            # Optionally remove the uncompressed file
            output_path.unlink()
            print(f"Removed uncompressed file {output_path}", file=sys.stderr)

        except Exception as e:
            print(f"Error compressing/indexing: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
