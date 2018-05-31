function getCorpAssets(){
	$.getJSON("/internal/industry/getCorpAssets", function(data){
		assets = data.assets
		translations = data.translations

		console.log(assets)
		console.log(translations)
		$.each(assets, function(k,v){
			bpc = ""
			if(v.is_blueprint_copy){
				bpc = "- BPC"
			}
			$(".assetsList").append("\
				<tr>\
					<td><img src='https://image.eveonline.com/Type/"+v.type_id+"_32.png'><br>"+translations[v.type_id]+""+bpc+"</td>\
					<td>"+translations[v.location_id]+"</td>\
					<td>"+v.quantity+"</td>\
					<td>"+v.location_flag+"<br>"+v.location_type+"<br>"+v.is_singleton+"</td>\
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