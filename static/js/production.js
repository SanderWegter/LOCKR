var typetimer
var typeinterval = 1000
var selID = ""
var val = ""
prodParts = {}
multipliers = {}

function getProduction(){
    $(".productionList").html("")
    $.getJSON("/internal/production/getProduction", function(data){
        $.each(data.production, function(k,v){
            var inputMaterials = "<table class='table table-bordered'><tr>"
            maxproducable = []
            maxproducablebuild = []
            $.each(v, function(key,val){
                if (!(key in prodParts)){
                    prodParts[key] = {'stock': 0, 'build': 0, 'required': 0}
                }
                prodParts[key]["stock"] = val.stock
                prodParts[key]["build"] = val.inbuild
                prodParts[key]["required"] += val.quantity * data.toProduce[k].quantity
                multipliers[data.toProduce[k].dbid] = data.toProduce[k].quantity
                clr = "green"
                if (val.stock >= (val.quantity * data.toProduce[k].quantity)){
                    stockquan = "<font color='"+clr+"'>"+val.stock+"/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducable.push(Math.floor(val.stock / (val.quantity * data.toProduce[k].quantity)))
                    producable = "<br>"+Math.floor(val.stock / (val.quantity * data.toProduce[k].quantity))
                }
                else{
                    clr = "red"
                    stockquan = "<font color='"+clr+"'>"+val.stock+"/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducable.push(0)
                    producable = ""
                }

                inprod = ""
                if (val.inbuild > 0){
                    stockquan = "<font color='"+clr+"'>"+val.stock+"(+"+val.inbuild+")/"+(val.quantity * data.toProduce[k].quantity)+"</font>"
                    maxproducablebuild.push(Math.floor((val.stock + val.inbuild) / (val.quantity * data.toProduce[k].quantity)))
                }

                inputMaterials += "<td><img src='https://image.eveonline.com/Type/"+key+"_32.png' title='"+data.translations[key].name+"'><br>"+stockquan+""+producable+"</td>"
            })
            
            
            inputMaterials += "</tr></table>"
            $(".productionList").append("\
                                            <tr>\
                                            <td><input type='number' min=0 value='"+data.toProduce[k].quantity+"' id='dbid"+data.toProduce[k].dbid+"'></td>\
                                            <td><img src='https://image.eveonline.com/Type/"+k+"_32.png'><br>"+data.translations[k].name+"<br>"+Math.min(...maxproducable)+"("+Math.min(...maxproducablebuild)+")</td>\
                                            <td>"+inputMaterials+"</td>\
                                            </tr>\
            ")
        })
        $.each(prodParts, function(k,v){
            $(".partsList").append("<tr>\
                                        <td><img src='https://image.eveonline.com/Type/"+k+"_32.png' title='"+data.translations[k].name+"'></td>\
                                        <td>"+v.stock+"</td>\
                                        <td>"+v.build+"</td>\
                                        <td>"+v.required+"</td>\
                                        <td>"+(v.required - v.build - v.stock)+"</td>\
                                    </tr>")
        })
        $(":input[id^='dbid']").bind('keyup mouseup', function(){
            selID = (this.id).split("dbid")[1]
            val = $("#dbid"+selID).val()
            clearTimeout(typetimer);
            typetimer = setTimeout(function(){
                $.getJSON("/interal/production/setTarget/"+selID+"/"+val, function(){
                    getProduction()
                })
            }, typeinterval)
        })
    })
}

$(document).ready(function(){
    getProduction()
    
})