function getCorpAssets(){
	$.getJSON("/internal/industry/getCorpAssets", function(data){
		assets = data.assets
		translations = data.translations

		console.log(assets)
		console.log(translations)
		$.each(assets, function(k,v){
			$(".assetsList").append("\
				<tr>\
					<td>"+translations[v.type_id]+"</td>\
					<td>"+translations[v.location_id]+"</td>\
					<td>"+v.quantity+"</td>\
					<td>"+v.location_flag+"<br>"+v.location_type+"</td>\
				</tr>\
				")
			$("#assetTable").DataTable({
        		'paging': true,
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
	})
}

$(document).ready(function(){
	getCorpAssets()
})