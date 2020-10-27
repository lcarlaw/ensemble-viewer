window.local = Object.assign({}, window.local, {
    module: {
        set_style: function(feature) {
            return {
                fillColor: feature.properties.fill,
                color: 'black',
                opacity: 0.7,
                stroke: true,
            };
        }
    }
});
