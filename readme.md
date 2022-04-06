# VFX Project1
B06607057 蘇鈺崴

## Enviroment
python 3.9 \
opencv 4.5.4\
numpy 1.16.6
## Usage
### 0. 
### 1. hdr.sh: Computing radience map to output.npy 
hdr.sh will save the radience map into output.npy and output.hdr.

    bash hdr.sh ${filepath} ${output}
Parameters: for sampling srow x scol for each pictures.
* srow : defalut 20
* scol :  defalut 20


### 2. tone.sh: for computing tonemapping to output.npy
tone.sh will save 3x2 different pictures into save directory.

    bash tone.sh ${hdr output name} ${save directory}

Parameters: Reinhard's tonemapping parameters.
* key : defalut 0.72
* white :  defalut 1
* phi : 8
* threshold : 0.05

### 3. hw1.sh: reproduce the hdr image for coach and road.
    
    bash tone.sh