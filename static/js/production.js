function getProduction(){
    $.getJSON("/internal/production/getProduction", function(data){
        $.each(data.production, function(k,v){
            var inputMaterials = "<table><tr>"
            $.each(v, function(key,val){
                if (val.stock > val.quantity){
                    stockquan = "<font color='green'>"+val.stock+"/"+val.quantity+"</font>"
                }
                else{
                    stockquan = "<font color='red'>"+val.stock+"/"+val.quantity+"</font>"
                }
                inputMaterials += "<td><img src='https://image.eveonline.com/Type/"+key+"_32.png'><br>"+data.translations[key].name + "<br>"+stockquan+"</td>"
            })
            inputMaterials += "</tr></table>"
            $(".productionList").append("\
                                            <tr>\
                                            <td><img src='https://image.eveonline.com/Type/"+k+"_32.png'><br>"+data.translations[k].name+"</td>\
                                            <td>"+inputMaterials+"</td>\
                                            </tr>\
            ")
        })
    })
}

$(document).ready(function(){
    getProduction()
})