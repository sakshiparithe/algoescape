let steps = 0;
let currentArray = [];

function generateArray(){
    fetch('/generate')
    .then(res => res.json())
    .then(data => {
        currentArray = data;
        displayArray(data);
        steps = Math.floor(Math.random() * 15) + 5; 
    });
}

function displayArray(arr){
    const arrayDiv = document.getElementById("array");
    arrayDiv.innerHTML = arr.map(num => 
        `<div class="array-box">${num}</div>`
    ).join('');
}

function finishGame(){
    fetch('/analyze',{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            steps:steps,
            array:currentArray
        })
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("result").innerHTML =
        "Optimal Steps: "+data.optimal_steps+
        " | Efficiency: "+data.efficiency+"%";
    });
}
