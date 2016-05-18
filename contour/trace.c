#include<stdio.h>
#include<stdlib.h>

int main(void){

    int imgH,imgW;
    int i,j;

    unsigned char **image;

    imgH = 1024;
    imgW = 1024;


    /* Create buffer for input image uint8 */
    if (image = (unsigned char **) malloc(sizeof(unsigned char *)*imgH)){
        for(i=0;i<imgH;i++){
            *image = (unsigned char *) malloc(sizeof(unsigned char)*imgW);
        }
    }

    
    /* Read image*/
    /* Todo: Pass the buffer through Python */





    /* Free the image memory */
    for(i=0;i<imgH;i++){
        free(image[i]);
    }
    free(image);

    return;
}
