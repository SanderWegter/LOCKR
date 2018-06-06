function getCorpAssets(){
	$.getJSON("/internal/industry/getCorpAssets", function(data){
		assets = data.assets
		translations = data.translations
		assetNames = data.assetnamelist
		divisions = data.divisions

		hangars = {}
		$.each(divisions.hangar, function(k,v){
			hangars[v["division"]] = v["name"]
		})

		console.log(assets)
		console.log(translations)
		$.each(assets, function(k,v){
			bpc = ""
			if(v.is_blueprint_copy){
				bpc = " - BPC"
			}
			var location = v.location_flag
			if ((v.location_flag).indexOf("CorpSAG")>=0){
				location = hangars[(v.location_flag).split("CorpSAG")[1]]
			}

			if (v.orig_location_id != undefined){
				console.log(assetNames[v.orig_location_id])
			}

			$(".assetsList").append("\
				<tr>\
					<td><img src='https://image.eveonline.com/Type/"+v.type_id+"_32.png'><br>"+translations[v.type_id]["name"]+""+bpc+"</td>\
					<td>"+translations[v.location_id]["name"]+"</td>\
					<td>"+v.quantity+"</td>\
					<td>"+location+"<br>"+v.location_type+"<br>"+v.is_singleton+"</td>\
					<td>"+translations[v.type_id]["group"]+"</td>\
				</tr>\
				")

        	})
			$("#assetsTable").DataTable({
            'paging': true,
            'pageLength': 25,
            'lengthChange': true,
            'searching': true,
            // 'ordering': true,
            // 'order': [[ 4, "desc" ]],
            'info': true,
            'autoWidth': true,
            'language': {
                'search': "_INPUT_",
                'searchPlaceholder': "Search..."
            }
		})
	})
}

$(document).ready(function(){
	getCorpAssets()
})