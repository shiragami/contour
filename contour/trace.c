#include<stdio.h>
#include<stdlib.h>
#define OFFSET 10
#define MAXSTEP 500
#define MINSTEP 50

unsigned char **img;
int imgH,imgW;
int count = 0;
FILE *fcontour;

void MooreTrace(int sx,int sy,int thres_min,int thres_max){

    /* Create clockwise neighbourhood, starts with north-west */
    int mx[8] = {-1,0,1,1,1,0,-1,-1};
    int my[8] = {1,1,1,0,-1,-1,-1,0};

    int contourx[MAXSTEP];
    int contoury[MAXSTEP];

    //imgcon = np.zeros([imgsize,imgsize,3])
    //contour = [[sx,sy]]
    //imgcon[sy,sx] = [0,255,0]

    /* Init starting point */
    int py = sy; int px = sx;
    int wy = sy; int wx = sx;

    /* Finishing criterion */
    int finish = 0;
    int step = 1;
    int fail;

    contourx[0] = sx;
    contoury[0] = sy;

    while(step<MAXSTEP && !finish){
        int c;
        fail = 1;
        for(c=0;c<8;c++){
            /* Rotate around p, clockwise */
            int cx = px + mx[c];
            int cy = py + my[c];

            /* Break if reach border */
            /* Todo: Can I just use return 0 ? */
            if(cx < 0 || cx > imgW-1 || cy < 0 || cy > imgH-1) break;
            
            /* Image thresholding */
            if(img[cy][cx] < thres_min || img[cy][cx] > thres_max){
                /* Background: Advance */
                wy = cy; wx = cx;
                //imgcon[cy,cx] = [0,0,255]
            }else{
                /* Foreground: Backtrack */
                //imgcon[py,px] = [0,255,0]
                //imgcon[cy,cx] = [0,255,0]
                py = wy; px = wx;
                //print py,px,step
                //printf("%d %d step=%d\n",py,px,step);
                // Todo:Append contour 
                //contour.append([px,py])        

                contourx[step] = px;
                contoury[step] = py;

                /* If cx & cy returns to seed with same direction as first step, flag finish */
                //if(cx == sx && cy == sy) finish = 1;
                if(cx == sx && cy == sy && mx[c] == -1 && my[c] == 1) finish = 1;

                //my,mx = shiftneighbour(my,mx,c)
                /* Shift neighbour when backtrack */
                int k,tmp[8];
                for(k=0;k<8;k++) tmp[k] = my[(k+c+5)%8];
                for(k=0;k<8;k++) my[k]  = tmp[k];

                //for(k=0;k<8;k++) tmp[k] = mx[(k+c+5)%8];
                //for(k=0;k<8;k++) mx[k]  = tmp[k];
                for(k=0;k<8;k++) mx[k]  = tmp[(k+6)%8];

                step++;
                fail = 0;
                break;
            }
        }
        if(fail) break; // This for breaking early do error
    }
    if(finish && step>MINSTEP){
        int i;
        /* Todo */
        //return True,imgcon,contour
        //sm.imsave("imgcon.png",imgcon)

        for(i=0;i<step;i++){
            //printf("%d %d,",contourx[i],contoury[i]);
            fprintf(fcontour,"%d %d,",contourx[i],contoury[i]);
            //fprintf(fcontour,"Test\n");
        }
        fprintf(fcontour,"\n");
        //printf("\n");

        count++;
        return;
    }
    
    return;
}

int main(int argc, char *argv[]){
    int i,j;

    if(argc!=4){
        printf("trace <imgfile> <imgheight> <imgwidth>\n");
        exit(1);
    }

    //printf("imgfile:%s\n",argv[1]);


    imgH = atoi(argv[2]);
    imgW = atoi(argv[3]);

    /* Create buffer for input image uint8 */
    if (img = (unsigned char **) malloc(sizeof(unsigned char *)*imgH)){
        for(i=0;i<imgH;i++){
            img[i] = (unsigned char *) malloc(sizeof(unsigned char)*imgW);
        }
    }

    /* Read image*/
    /* Todo: Pass the buffer through Python */
    FILE *fimg = fopen(argv[1],"rb");
    if(fimg == NULL){
        printf("Image not found\n");
        exit(1);
    }else{
        for(i=0;i<imgH;i++){
            for(j=0;j<imgW;j++){
                img[i][j] = fgetc(fimg);
                //printf("%d\n",img[i][j]);
            }
        }
    }
    fclose(fimg);

    /* Open file for output */
    fcontour = fopen("contour.dat","w");
    if(fcontour == NULL){
        printf("Error opening output file\n");
    }



    /* Search for local maxima */
    for(i=OFFSET;i<imgH-OFFSET;i++){
        int prev_intensity = img[i][0];
        int intensity = img[i][1];


        /* Initialize the extremal variables */
        int intensity_max_grad = intensity;
        int min_intensity = prev_intensity;
        int max_intensity = prev_intensity;
        int index_min_intensity = 0;
        int index_max_intensity = 0;
        int index_max_gradient = 0;
        int max_gradient = -1;

        for(j=OFFSET;j<imgW-OFFSET;j++){
            /* Read and store the value of next pixel */
            int next_intensity = img[i][j+1];

            /* Update value and position of min intensity */
            if(intensity < min_intensity){
                min_intensity = intensity;
                index_min_intensity = j;
            }

            /* Update value and position of max intensity */
            if(intensity > max_intensity){
                max_intensity = intensity;
                index_max_intensity = j;
            }
        
            /* Calculate local gradient */
            int gradient = intensity - prev_intensity;

            /* Turn negative grad to positive */
            if(gradient < 0) gradient = -gradient;

            /* Update position and value of max local gradient */
            if(gradient > max_gradient){
                max_gradient = gradient;
                index_max_gradient = j;
                intensity_max_grad = intensity;
            }

            /* Determine if slope is + or - */
            int increasing = index_min_intensity < index_max_intensity ? 1:0;

            /* Start contour tracing if local maxima is reached */
            int min_obj_intensity,max_obj_intensity;
            if ((increasing && next_intensity<intensity) || (!increasing && next_intensity>intensity)){
                if(increasing){
                    //print "up"
                    min_obj_intensity = intensity_max_grad;
                    max_obj_intensity = max_intensity;
                }else{
                    //print "down"
                    min_obj_intensity = min_intensity;
                    max_obj_intensity = intensity_max_grad;
                }

                /* Start tracing */
                //Todo: 
                //flag,imgcon,contour = MooreTrace(img,index_max_gradient,v,min_obj_intensity,max_obj_intensity)
                MooreTrace(index_max_gradient,i,min_obj_intensity-0,max_obj_intensity+0);

                /* Mark max local gradient */
                //img_grad[v,index_max_gradient] = [0,255,0]

                //Todo:
                /*
                if flag:
                    print "Tracing succeed"
                    fname =  "./contour/imgcon_" + "{0:04d}".format(ncontour) + ".png"
                    sm.imsave(fname,imgcon)
                    fname =  "./contour/cont_" + "{0:04d}".format(ncontour) + ".dat"
                    np.savetxt(fname,contour,fmt="%d")
                    ncontour = ncontour + 1
                */

                /* Reset variable */
                min_intensity = intensity;
                max_intensity = intensity;
                index_min_intensity = j;
                index_max_intensity = j;
                max_gradient = -1;
            }

            prev_intensity = intensity;
            intensity = next_intensity;

        }

    }


    /* Free the image memory */
    for(i=0;i<imgH;i++){
        free(img[i]);
    }
    free(img);

    //printf("Contour found:%d\n",count);

    fclose(fcontour);
    return;
}
