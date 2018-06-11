function getProduction(){
    $.getJSON("/internal/production/getProduction", function(data){
        $.each(data.production, function(k,v){
            var inputMaterials = "<table><tr>"
            maxproducable = []
            maxproducablebuild = []
            $.each(v, function(key,val){
                if (val.stock >= val.quantity){
                    stockquan = "<font color='green'>"+val.stock+"/"+val.quantity+"</font>"
                    maxproducable.push(Math.floor(val.stock / val.quantity))
                    producable = "<br>"+Math.floor(val.stock / val.quantity)
                }
                else{
                    stockquan = "<font color='red'>"+val.stock+"/"+val.quantity+"</font>"
                    maxproducable.push(0)
                    producable = ""
                }

                inprod = ""
                if (val.inbuild > 0){
                    stockquan += "("+val.inbuild+")"
                    maxproducablebuild.push(Math.floor((val.stock + val.inbuild / val.quantity)))
                }

                inputMaterials += "<td><img src='https://image.eveonline.com/Type/"+key+"_32.png'><br>"+data.translations[key].name + "<br>"+stockquan+""+producable+"</td>"
            })
            inputMaterials += "</tr></table>"
            $(".productionList").append("\
                                            <tr>\
                                            <td><img src='https://image.eveonline.com/Type/"+k+"_32.png'><br>"+data.translations[k].name+"<br>"+Math.min(...maxproducable)+"("+Math.min(...maxproducablebuild)+")</td>\
                                            <td>"+inputMaterials+"</td>\
                                            </tr>\
            ")
        })
    })
}

$(document).ready(function(){
    getProduction()
})