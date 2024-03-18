#!/bin/bash

set -e
trap 'echo "Script submit_all_ho.sh exited with error: $?" >&2; exit $?' ERR

derivatives="${SINGULARITY_HOME}/CCIR_01211/derivatives"
subs=("sub-108293" "sub-108237" "sub-108250" "sub-108306")
avrc="1"
if_types=("twil" "idif")
proc="trc-fdg_proc-delay0-BrainMoCo2-createNiftiMovingAvgFrames*-ParcSchaeffer-reshape-to-schaeffer-schaeffer.nii.gz"
submit_main="${HOME}/PycharmProjects/dynesty/idif2024/submit_main_async_96h.sh"

for sub in "${subs[@]}"; do
  containing_folder="$derivatives/$sub"
  files=()

  # use a while-read loop to feed the find results into the array
  while IFS= read -r line; do
      files+=("$line")
  done < <(find "$containing_folder" -type f -name "*$proc*")

  for afile in "${files[@]}"; do
    for type in "${if_types[@]}"; do
      echo "sbatch \"${submit_main}\" \"${type}\" \"${afile}\" \"${avrc}\""
      sbatch "${submit_main}" "${type}" "${afile}" "${avrc}"
    done
  done
done
