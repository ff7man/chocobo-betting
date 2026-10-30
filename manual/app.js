const BET_PAIRS=['1-2','1-3','1-4','1-5','1-6','2-3','2-4','2-5','2-6','3-4','3-5','3-6','4-5','4-6','5-6'];
const COLORS=[
  {name:'Silver',color:'#718fca',rank:2},
  {name:'Gold',color:'#f0d43a',rank:3},
  {name:'Bronze',color:'#a96e3c',rank:1},
  {name:'Platinum',color:'#85878a',rank:4}
];
const PRIZE_SLOT_NAMES=['i','ii','iii'];
const SAMPLE_RACERS=[
  {name:'BLUES',speed:87,stamina:255,color:2,sprinting:false},
  {name:'GEORGE',speed:82,stamina:257,color:2,sprinting:false},
  {name:'JOEL',speed:76,stamina:250,color:0,sprinting:false},
  {name:'ARL',speed:81,stamina:261,color:2,sprinting:false},
  {name:'JAMES',speed:74,stamina:265,color:3,sprinting:true},
  {name:'YOUNG',speed:80,stamina:259,color:2,sprinting:false}
];
const racers=SAMPLE_RACERS.map(racer=>({...racer}));
const classSelect=document.querySelector('#class-select');
const betGrid=document.querySelector('#bet-grid');
const raceList=document.querySelector('#race-list');
const suggestedPairs=document.querySelector('#suggested-pairs');

function predictedPairs(){
  const eligible=racers.map((racer,index)=>({
    index:index+1,
    speed:Number(racer.speed)||0,
    jockey:COLORS[racer.color],
  })).filter(racer=>racer.jockey.name!=='Bronze');
  eligible.sort((a,b)=>b.speed-a.speed||b.jockey.rank-a.jockey.rank);
  const selected=eligible.slice(0,3);
  const pairs=[];
  for(let first=0;first<selected.length;first++){
    for(let second=first+1;second<selected.length;second++){
      pairs.push([selected[first].index,selected[second].index].sort((a,b)=>a-b).join('-'));
    }
  }
  return pairs;
}

function updateBetGrid(){
  const rank=classSelect.value.toLowerCase();
  const predicted=predictedPairs();
  const bronzeNumbers=racers.flatMap((racer,index)=>COLORS[racer.color].name==='Bronze'?[index+1]:[]);
  betGrid.replaceChildren();
  BET_PAIRS.forEach(pair=>{
    const cell=document.createElement('div');
    cell.className='bet-cell';cell.dataset.betPair=pair;
    const tile=document.createElement('img');tile.className='tile-image';tile.alt=`Bet on chocobos ${pair}`;
    tile.src=`assets/class-${rank}/tiles/${pair}.png`;
    tile.onerror=()=>{tile.onerror=null;tile.src=`assets/class-${rank==='c'?'b':'c'}/tiles/${pair}.png`;};
    cell.append(tile);
    if(pair.split('-').some(id=>bronzeNumbers.includes(Number(id))))cell.classList.add('has-bronze');
    if(predicted.includes(pair))cell.classList.add('is-predicted');
    betGrid.append(cell);
  });
  suggestedPairs.textContent=predicted.length?predicted.join(' · '):'No pair (fewer than two non-Bronze racers)';
}

function updateRacerCard(index){
  const racer=racers[index];
  const color=COLORS[racer.color];
  const card=document.createElement('article');card.className='racer-card';
  const heading=document.createElement('div');heading.className='racer-heading';
  const avatar=document.createElement('img');avatar.className=`racer-avatar${index===1?' racer-avatar--2':''}`;
  avatar.src=`assets/racer-icons/${index+1}.png`;avatar.alt='';
  const number=document.createElement('span');number.className='racer-number';number.textContent=String(index+1).padStart(2,'0');
  heading.append(avatar,number);

  const nameRow=document.createElement('label');nameRow.className='racer-input-row';
  const nameCaption=document.createElement('span');nameCaption.textContent='NAME';
  const name=document.createElement('input');name.className='racer-name';name.type='text';name.maxLength=12;name.value=racer.name;name.setAttribute('aria-label',`Chocobo ${index+1} name`);
  name.addEventListener('input',()=>{racers[index].name=name.value;});
  nameRow.append(nameCaption,name);

  const stats=document.createElement('div');stats.className='racer-stats';
  for(const [label,key,max] of [['SPD','speed',999],['STA','stamina',9999]]){
    const wrapper=document.createElement('label');wrapper.className='racer-stat';
    const caption=document.createElement('span');caption.textContent=label;
    const input=document.createElement('input');input.type='number';input.min='0';input.max=String(max);input.step='1';input.value=String(racer[key]);input.setAttribute('aria-label',`Chocobo ${index+1} ${key}`);
    input.addEventListener('input',()=>{racers[index][key]=input.value===''?0:Number(input.value);updateBetGrid();});
    wrapper.append(caption,input);stats.append(wrapper);
  }

  const colorButton=document.createElement('button');colorButton.className='color-button';colorButton.type='button';
  colorButton.setAttribute('aria-label',`Chocobo ${index+1} jockey: ${color.name}. Click to change color.`);
  const swatch=document.createElement('span');swatch.className='jockey-swatch';swatch.style.backgroundColor=color.color;
  const colorName=document.createElement('span');colorName.className='jockey-name';colorName.textContent=color.name;
  colorButton.append(swatch,colorName);
  colorButton.addEventListener('click',()=>{racers[index].color=(racers[index].color+1)%COLORS.length;renderRacers();updateBetGrid();});

  const sprintButton=document.createElement('button');sprintButton.className=`sprint-button${racer.sprinting?' is-sprinting':''}`;sprintButton.type='button';
  sprintButton.setAttribute('aria-pressed',String(racer.sprinting));
  sprintButton.textContent=racer.sprinting?'SPRINTING':'NOT SPRINTING';
  sprintButton.addEventListener('click',()=>{racers[index].sprinting=!racers[index].sprinting;renderRacers();});

  card.append(heading,nameRow,stats,colorButton,sprintButton);return card;
}

function renderRacers(){
  raceList.replaceChildren(...racers.map((_,index)=>updateRacerCard(index)));
}

function updateClassTheme(){
  document.body.dataset.rank=classSelect.value;
  renderRacers();updateBetGrid();
}

classSelect.addEventListener('change',updateClassTheme);
renderRacers();updateBetGrid();
