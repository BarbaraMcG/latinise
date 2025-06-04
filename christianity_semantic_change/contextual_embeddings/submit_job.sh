#### submit_job.sh START ####
#!/bin/bash
#$ -cwd
# error = Merged with joblog
#$ -o joblog.$JOB_ID
#$ -j y
## Edit the line below as needed:
#$ -l h_rt=1:00:00,h_data=24G,gpu,A100
## Modify the parallel environment
## and the number of cores as needed:
#$ -pe shared 6
# Email address to notify
#$ -M $USER@mail
# Notify when
#$ -m bea

# echo job info on joblog:
echo "Job $JOB_ID started on:   " `hostname -s`
echo "Job $JOB_ID started on:   " `date `
echo " "

# load the job environment:
. /u/local/Modules/default/init/modules.sh
## Edit the line below as needed:
module load python/3.9.6

## substitute the command to run your code
## in the two lines below:
echo 'python /u/home/v/vlunardi/latin-bert-finetuning/embeddings_pre-trained.py'
python /u/home/v/vlunardi/latin-bert-finetuning/embeddings_pre-trained.py

# echo 'python /u/home/v/vlunardi/latin-bert-finetuning/embeddings_fine-tuned.py'
# python /u/home/v/vlunardi/latin-bert-finetuning/embeddings_fine-tuned.py

# echo job info on joblog:
echo "Job $JOB_ID ended on:   " `hostname -s`
echo "Job $JOB_ID ended on:   " `date `
echo " "
#### submit_job.sh STOP ####