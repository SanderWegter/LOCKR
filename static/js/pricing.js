minerals = {34: 'tritIsk', 35: 'pyeIsk', 36: 'mexIsk', 37: 'isoIsk', 38: 'nocxIsk', 39: 'zydIsk', 40: 'megaIsk'}

function getPrices() {
    $(".priceList").html("")
    $.getJSON("/internal/market/getPricingInfo", function(data) {
        items = data.items
        console.log(items)
        translations = data.translations
        $.each(items, function(k, v) {
            if (minerals[k] != undefined) {
            	console.log(minerals[k])
            	$("."+minerals[k]).html("buy: "+ v.iskBuy+"<br>sell: "+v.iskSell)
                return true
            }
            console.log(k)
            console.log(v)
            buildcost = 0
            $.each(v.materials, function(key,val){
            	buildcost += val * items[key]["iskBuy"]
            })

            if (buildcost < v.iskBuy){
            	buy = "danger"
            	build = "success"
            }
            else{
            	buy = "success"
            	build = "danger"
            }

            $(".priceList").append(
                "<tr>\
						<td><img src='https://image.eveonline.com/Type/" + k + "_32.png'><br>" + translations[k]["name"] + "</td>\
						<td class='"+buy+"'>Buy: " + convertCurrency(v.iskBuy) + "<br>Sell: "+ convertCurrency(v.iskSell)+"</td>\
						<td class='"+build+"'>"+convertCurrency(buildcost)+"</td>\
						<td><button class='btn btn-xs btn-danger' onclick='delItem(\"" + k + "\")'>Delete</button></td>\
					</tr>"
            )
        })
    })
}

function getItemList() {
    $("#itemList").select2({
        width: '100%',
        minimumInputLength: 3,
        ajax: {
            url: '/internal/market/getMarketItems',
            dataType: 'json',
            results: function(data) {
                return { results: data }
            }
        }
    })
}

function updatePrices() {
    $(".priceList").html("")
    $("#spinRefresh").addClass("fa-spin")
    $.getJSON("/internal/market/updatePrice", function(data){
    	$("#spinRefresh").removeClass("fa-spin")
    	getPrices()
    })
}

function postItems() {
    $(".priceList").html("")
    items = $("#itemList").val()
    post = {
        "items": items
    }
    $.post("/internal/market/postMarketItems", post, function() {
        $("#itemList").val(null).trigger('change');
        getPrices()
    }, "json")
}

function delItem(itemID) {
    $(".priceList").html("")
    $.getJSON("/internal/market/delMarketItem/" + itemID, function() {
        getPrices()
    })
}

function convertCurrency(amount) {
    if (amount >= 1000000 || amount <= -1000000) {
        if (amount >= 1000000000 || amount <= -1000000000) {
            amount = (amount / 1000000000).toFixed(3) + "B"
        } else {
            amount = (amount / 1000000).toFixed(3) + "M"
        }

    }
    return amount
}

$(document).ready(function() {
    getPrices()
    getItemList()
})