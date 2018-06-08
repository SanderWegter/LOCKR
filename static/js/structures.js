function getStructures(){
    $.getJSON("/internal/structures/getStructures", function(data){
        console.log(data)
    })
}

$(document).ready(function(){
    getStructures()
})