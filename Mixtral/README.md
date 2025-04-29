This is code implemented for Mixtral 8x7B Model.

1. Download Mixtral 8x7B hugging face version and put all model files into `MixtralModel` file folder.

2. Lauch the backend program for LLM service: `CUDA_VISIBLE_DEVCIES=gpuids python mixtral_server_multi.py &`
   (This program will occupy port 33331 of your machine)

3. Do the Evidence Abstraction (as preprocess):
    `python extract_key_info_mixtral_part1.py [--fs]`
   `python extract_key_info_mixtral_part2.py [--fs]`

4. Run the model with:

   `python run.py [--fs]`

5. Evaluate the result with:

   `python analyzerecord.py [--fs]`

If test on HOVER dataset do not apply `[--fs]`  ! fs means Feverous-S