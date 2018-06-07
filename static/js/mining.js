function getMining(){
    $.getJSON("/internal/mining/getMoonMining", function(data){
        console.log(data)
    })
}

$(document).ready(function(){
    getMining()
})