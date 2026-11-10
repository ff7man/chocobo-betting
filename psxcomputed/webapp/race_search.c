#include <stdint.h>
#include <stddef.h>

typedef struct { int id, special, weight, move_last; } Reward;
static const Reward C[]={{23,0,5,1},{8,0,20,1},{21,0,10,0},{22,0,10,0},{20,0,20,0},{11,0,5,1},{12,0,5,0},{13,0,5,0},{19,0,5,1},{20,0,20,1}};
static const Reward B[]={{8,0,30,0},{10,0,10,0},{20,0,20,0},{18,0,5,1},{8,0,30,0},{23,0,5,0},{21,0,10,0},{22,0,10,0},{23,0,5,0},{11,0,10,1},{12,0,10,0},{13,0,10,0},{9,0,10,1},{5,1,5,1},{23,0,5,0}};
static const Reward A[]={{8,0,20,0},{10,0,10,0},{14,1,10,0},{15,1,10,0},{12,0,10,0},{16,1,10,0},{1,0,10,1},{5,1,5,1},{11,0,10,0},{12,0,10,0},{13,0,10,0},{9,0,10,1},{23,0,5,0},{8,0,20,0},{0,1,7,1},{9,0,5,1},{20,0,20,0},{12,0,10,0},{4,1,7,1},{6,1,7,1}};
static const Reward S[]={{18,1,5,0},{10,0,5,0},{9,0,5,1},{1,0,5,1},{5,1,5,1},{6,1,5,1},{14,1,5,0},{15,1,5,0},{11,0,2,0},{15,1,5,0},{20,0,20,0},{16,0,5,0},{17,1,5,1},{18,0,5,0},{0,1,5,1},{14,0,5,0},{4,1,5,1},{9,0,5,1},{7,1,5,1},{16,1,5,0},{3,1,5,1},{2,1,5,1}};
static const int BASE[4]={0x09c4,0x0bb8,0x0dac,0x1388};
static const int RANGE[4]={0x01f4,0x0258,0x02bc,0x0320};
static const int SPEED_BASE[4]={0x06a4,0x0898,0x0bb8,0x0fa0};
static const int SPEED_RANGE[4]={0x00c8,0x012c,0x01f4,0x01f4};
static const Reward* TABLES[4]={C,B,A,S};
static const int TABLE_SIZES[4]={10,15,20,22};
static inline uint32_t next(uint32_t *state){*state=*state*0x41c64e6du+0x3039u;return (*state>>16)&0x7fffu;}

static int matches_seed(uint32_t seed,int rank,int target_speed,int target_stamina,int target_name,const int wanted[3]){
  uint32_t state=seed;
  for(int i=0;i<0x28;i++){next(&state);next(&state);}
  int dash=BASE[rank];
  int ds=dash+(int)(next(&state)%RANGE[rank]);
  next(&state); next(&state);
  int st=dash+(int)(next(&state)%300);
  next(&state); next(&state);
  if(ds/34!=target_speed||st/10!=target_stamina)return 0;
  for(int i=1;i<6;i++){next(&state);next(&state);next(&state);next(&state);next(&state);next(&state);}
  int names[43];for(int i=0;i<43;i++)names[i]=i;
  for(int i=0;i<0xc8;i++){int a=(int)(next(&state)%43),b=(int)(next(&state)%43),tmp=names[a];names[a]=names[b];names[b]=tmp;}
  if(names[0]!=target_name)return 0;
  if(wanted[0]<0&&wanted[1]<0&&wanted[2]<0)return 1;
  const Reward *table=TABLES[rank]; int n=TABLE_SIZES[rank],selected=0,move_last_id=-1;
  int pool[3]={255,255,255};
  while(selected<3){
    const Reward item=table[next(&state)%n];
    int duplicate=0;for(int i=0;i<selected;i++)if(pool[i]==item.id)duplicate=1;
    if(duplicate)continue;
    if(move_last_id!=-1&&item.move_last)continue;
    pool[selected++]=item.id;
    if(item.move_last)move_last_id=item.id;
  }
  for(int i=0;i<3;i++)for(int j=i+1;j<3;j++)if(pool[i]>pool[j]){int tmp=pool[i];pool[i]=pool[j];pool[j]=tmp;}
  if(move_last_id>=0){for(int i=0;i<2;i++)if(pool[i]==move_last_id){int tmp=pool[i];pool[i]=pool[2];pool[2]=tmp;break;}}
  for(int i=0;i<3;i++)if(wanted[i]>=0&&wanted[i]!=pool[i])return 0;
  return 1;
}

// Returns 0 when no match exists in this batch; otherwise returns offset + 1.
__attribute__((export_name("scan")))
uint32_t scan(uint32_t start,uint32_t count,int rank,int target_speed,int target_stamina,int target_name,int p0,int p1,int p2){
  const int wanted[3]={p0,p1,p2};
  for(uint32_t offset=0;offset<count;offset++)
    if(matches_seed(start+offset,rank,target_speed,target_stamina,target_name,wanted))return offset+1;
  return 0;
}
